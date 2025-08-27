#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: auth/microsoft_auth.py
💾 FUNÇÃO: Autenticação Microsoft Graph API para ENEL
🔧 DESCRIÇÃO: Gerenciamento de tokens, refresh e credenciais Microsoft
👨‍💼 AUTOR: Adaptado do BRK para ENEL
🔒 BASEADO EM: brk-render-seguro/auth/microsoft_auth.py
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, Optional
import hashlib
from datetime import datetime
import base64
from cryptography.fernet import Fernet

class MicrosoftAuth:
    """
    Gerenciador de autenticação Microsoft Graph API para ENEL
    
    Responsabilidades:
    - Carregar e salvar tokens no persistent disk
    - Renovar access_token usando refresh_token
    - Validar credenciais via environment variables
    - Manter estado de autenticação seguro
    - Adaptar configurações específicas do ENEL
    """
    
    def __init__(self):
        """Inicializar autenticação ENEL com validação obrigatória"""
        
        # CONFIGURAÇÕES APENAS VIA ENVIRONMENT VARIABLES
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.tenant_id = os.getenv("MICROSOFT_TENANT_ID", "consumers")
        
        # CONFIGURAÇÕES ESPECÍFICAS ENEL
        self.pasta_enel_id = os.getenv("PASTA_ENEL_ID")
        
        # VALIDAÇÃO OBRIGATÓRIA
        if not self.client_id:
            print("⚠️ MICROSOFT_CLIENT_ID não configurado - use /upload-token")
        
        # Caminhos para tokens (persistent disk prioritário)
        self.token_file_persistent = "/opt/render/project/storage/enel_token.json"
        self.token_file_local = "token.json"
        
        # Estado de autenticação
        self.access_token = None
        self.refresh_token = None
        
        # Carregar tokens existentes
        tokens_ok = self.carregar_token()
        
        print(f"🔐 Microsoft Auth ENEL inicializado")
        print(f"   Client ID: {'configurado' if self.client_id else 'pendente'}")
        print(f"   Tenant: {self.tenant_id}")
        print(f"   Pasta ENEL: {'configurada' if self.pasta_enel_id else 'pendente'}")
        print(f"   Token: {'✅ OK' if tokens_ok else '❌ Faltando'}")

    def _get_encryption_key(self):
        """Obter ou gerar chave de criptografia específica ENEL"""
        key_file = "/opt/render/project/storage/.enel_encryption_key"
        try:
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    return f.read()
            
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            return key
        except Exception:
            # Fallback: gerar chave determinística para ENEL
            unique_data = f"ENEL{self.client_id or 'default'}{os.getenv('RENDER_SERVICE_ID', 'fallback')}"
            return base64.urlsafe_b64encode(hashlib.sha256(unique_data.encode()).digest())

    def _encrypt_token_data(self, token_data):
        """Criptografar dados do token ENEL"""
        try:
            key = self._get_encryption_key()
            cipher = Fernet(key)
            json_data = json.dumps(token_data).encode('utf-8')
            return cipher.encrypt(json_data)
        except Exception as e:
            print(f"⚠️ Erro criptografando token: {e}")
            return None

    def _decrypt_token_data(self, encrypted_data):
        """Descriptografar dados do token ENEL"""
        try:
            key = self._get_encryption_key()
            cipher = Fernet(key)
            decrypted_data = cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            print(f"⚠️ Erro descriptografando token: {e}")
            return None
    
    def carregar_token(self) -> bool:
        """
        Carregar token do persistent disk ou local
        
        Prioridade para ENEL:
        1. /opt/render/project/storage/enel_token.json (persistent disk)
        2. ./token.json (local para desenvolvimento)
        
        Returns:
            bool: True se tokens carregados com sucesso
        """
        if os.path.exists(self.token_file_persistent):
            return self._carregar_do_arquivo(self.token_file_persistent)
        elif os.path.exists(self.token_file_local):
            return self._carregar_do_arquivo(self.token_file_local)
        else:
            print("💡 Token ENEL não encontrado - use interface web para upload")
            return False
    
    def _carregar_do_arquivo(self, filepath: str) -> bool:
        """
        Carregar token de arquivo específico (com suporte a criptografia)
        """
        try:
            # 🔐 NOVA LÓGICA: Tentar carregar arquivo criptografado primeiro
            encrypted_file = filepath.replace('.json', '.enc')
            if os.path.exists(encrypted_file):
                with open(encrypted_file, 'rb') as f:
                    encrypted_data = f.read()
                token_data = self._decrypt_token_data(encrypted_data)
                if token_data:
                    self.access_token = token_data.get('access_token')
                    self.refresh_token = token_data.get('refresh_token')
                    if self.access_token and self.refresh_token:
                        print(f"🔒 Token ENEL CRIPTOGRAFADO carregado de: {encrypted_file}")
                        return True
            
            # Fallback: carregar arquivo JSON original
            with open(filepath, 'r') as f:
                token_data = json.load(f)
            
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            if self.access_token and self.refresh_token:
                print(f"✅ Tokens ENEL carregados de: {filepath}")
                return True
            else:
                print(f"❌ Tokens ENEL incompletos em: {filepath}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON inválido em {filepath}: {e}")
            return False
        except Exception as e:
            print(f"❌ Erro carregando {filepath}: {e}")
            return False            
     
    def salvar_token_persistent(self) -> bool:
        """
        Salvar token ENEL no persistent disk com proteção de segurança E CRIPTOGRAFIA
        """
        try:
            # 🔒 PROTEÇÃO: Proteger diretório
            token_dir = os.path.dirname(self.token_file_persistent)
            os.makedirs(token_dir, exist_ok=True)
            os.chmod(token_dir, 0o700)  # Apenas proprietário
            
            token_data = {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'expires_in': 3600,
                'token_type': 'Bearer',
                'scope': 'https://graph.microsoft.com/.default offline_access',
                # 🔒 Metadados de segurança ENEL:
                'saved_at': datetime.now().isoformat(),
                'sistema': 'ENEL',
                'client_hash': hashlib.sha256((self.client_id or 'default').encode()).hexdigest()[:8],
                'pasta_enel_id': self.pasta_enel_id
            }
            
            # 🔐 NOVA LÓGICA: Tentar salvar criptografado primeiro
            encrypted_data = self._encrypt_token_data(token_data)
            if encrypted_data:
                encrypted_file = self.token_file_persistent.replace('.json', '.enc')
                with open(encrypted_file, 'wb') as f:
                    f.write(encrypted_data)
                os.chmod(encrypted_file, 0o600)
                # Remover arquivo antigo não criptografado se existir
                if os.path.exists(self.token_file_persistent):
                    os.remove(self.token_file_persistent)
                print(f"🔒 Token ENEL salvo CRIPTOGRAFADO: {encrypted_file}")
            else:
                # Fallback: salvar sem criptografia
                with open(self.token_file_persistent, 'w') as f:
                    json.dump(token_data, f, indent=2)
                os.chmod(self.token_file_persistent, 0o600)
                print(f"💾 Token ENEL salvo com proteção: {self.token_file_persistent}")
            
            return True
        except Exception as e:
            print(f"❌ Erro salvando token ENEL protegido: {e}")
            return False
            
    def atualizar_token(self) -> bool:
        """
        Renovar access_token usando refresh_token
        
        Utiliza refresh_token para obter novo access_token
        sem necessidade de reautenticação manual
        
        Returns:
            bool: True se renovação bem-sucedida
        """
        if not self.refresh_token:
            print("❌ Refresh token ENEL não disponível")
            return False
        
        try:
            url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            data = {
                'client_id': self.client_id,
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'scope': 'https://graph.microsoft.com/.default offline_access'
            }
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Atualizar access_token
                self.access_token = token_data['access_token']
                
                # Atualizar refresh_token se fornecido
                if 'refresh_token' in token_data:
                    self.refresh_token = token_data['refresh_token']
                
                # Salvar no persistent disk
                self.salvar_token_persistent()
                
                print("✅ Token ENEL renovado com sucesso")
                return True
                
            else:
                print(f"❌ Erro renovando token ENEL: HTTP {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Detalhes: {error_detail.get('error_description', 'N/A')}")
                except:
                    pass
                return False
                
        except requests.RequestException as e:
            print(f"❌ Erro de rede na renovação ENEL: {e}")
            return False
        except Exception as e:
            print(f"❌ Erro inesperado na renovação ENEL: {e}")
            return False
    
    def validar_token(self) -> bool:
        """
        Validar se access_token atual está funcional
        
        Faz uma requisição simples para verificar validade
        
        Returns:
            bool: True se token válido
        """
        if not self.access_token:
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception:
            return False
    
    def obter_headers_autenticados(self) -> Dict[str, str]:
        """
        Obter headers HTTP com autenticação
        
        Inclui tentativa automática de renovação se token expirado
        
        Returns:
            Dict[str, str]: Headers prontos para requisições Graph API
        """
        if not self.access_token:
            raise ValueError("❌ Access token ENEL não disponível")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        return headers
    
    def tentar_renovar_se_necessario(self, response_status: int) -> bool:
        """
        Tentar renovar token se requisição retornou 401
        
        Helper para uso em processadores que detectam token expirado
        
        Args:
            response_status (int): Status HTTP da requisição que falhou
            
        Returns:
            bool: True se renovação foi bem-sucedida
        """
        if response_status == 401:
            print("🔄 Token ENEL expirado detectado, tentando renovar...")
            return self.atualizar_token()
        
        return False
    
    def testar_acesso_pasta_enel(self) -> Dict:
        """
        Testar acesso específico à pasta ENEL
        
        Returns:
            Dict: Informações sobre acesso à pasta ENEL
        """
        if not self.access_token:
            return {
                "sucesso": False,
                "erro": "Token não disponível"
            }
        
        if not self.pasta_enel_id:
            return {
                "sucesso": False,
                "erro": "PASTA_ENEL_ID não configurada"
            }
        
        try:
            headers = self.obter_headers_autenticados()
            
            # Testar acesso à pasta específica ENEL
            url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_enel_id}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                pasta_info = response.json()
                return {
                    "sucesso": True,
                    "pasta_nome": pasta_info.get('displayName', 'N/A'),
                    "pasta_id": self.pasta_enel_id,
                    "total_mensagens": pasta_info.get('totalItemCount', 0),
                    "nao_lidas": pasta_info.get('unreadItemCount', 0)
                }
            else:
                return {
                    "sucesso": False,
                    "erro": f"Erro acessando pasta ENEL: HTTP {response.status_code}",
                    "pasta_id": self.pasta_enel_id
                }
                
        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro testando acesso pasta ENEL: {str(e)}"
            }
    
    def status_autenticacao(self) -> Dict:
        """
        Obter status atual da autenticação ENEL
        
        Returns:
            Dict: Informações sobre estado da autenticação
        """
        return {
            "sistema": "ENEL",
            "client_id_configurado": bool(self.client_id),
            "client_id_protegido": f"{self.client_id[:8]}******" if self.client_id else "N/A",
            "tenant_id": self.tenant_id,
            "pasta_enel_configurada": bool(self.pasta_enel_id),
            "pasta_enel_id": self.pasta_enel_id,
            "access_token_presente": bool(self.access_token),
            "refresh_token_presente": bool(self.refresh_token),
            "arquivo_token_persistent": os.path.exists(self.token_file_persistent),
            "arquivo_token_local": os.path.exists(self.token_file_local),
            "token_valido": self.validar_token() if self.access_token else False
        }