"""
Microsoft Authentication Manager - Versão Unificada Segura
Implementa persistência via OneDrive compartilhado (pasta Alerta) e criptografia Fernet
Para uso em CCB Alerta, BRK e Enel - Render deployment

Recursos:
- Token compartilhado na pasta Alerta (ONEDRIVE_ALERTA_ID)
- Criptografia Fernet com chave única por ambiente
- Logs sanitizados (tokens mascarados)
- Auto-migração de tokens legados
- Fallback local para contingência
"""

import os
import json
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

class MicrosoftAuthUnified:
    """
    Gerenciador de autenticação Microsoft unificado com:
    - Persistência via OneDrive compartilhado (pasta Alerta)
    - Criptografia Fernet obrigatória
    - Logs seguros com mascaramento
    - Compatibilidade com tokens legados
    """
    
    def __init__(self, client_id: str = None, client_secret: str = None, tenant_id: str = None):
        # Configurações via environment variables
        self.client_id = client_id or os.getenv("MICROSOFT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("MICROSOFT_CLIENT_SECRET") 
        self.tenant_id = tenant_id or os.getenv("MICROSOFT_TENANT_ID", "common")
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        self.alerta_folder_id = os.getenv("ONEDRIVE_ALERTA_ID")
        
        # Arquivo compartilhado na pasta Alerta
        self.shared_token_filename = "token.json"
        self.local_fallback_path = "token_backup.json"
        
        # Validações críticas
        if not self.client_id:
            raise ValueError("❌ MICROSOFT_CLIENT_ID não encontrado nas environment variables")
        if not self.encryption_key:
            raise ValueError("❌ ENCRYPTION_KEY não encontrada nas environment variables")
        if not self.alerta_folder_id:
            raise ValueError("❌ ONEDRIVE_ALERTA_ID não encontrado nas environment variables")
            
        # Inicializar Fernet
        try:
            self.fernet = Fernet(self.encryption_key.encode())
        except Exception as e:
            raise ValueError(f"❌ ENCRYPTION_KEY inválida: {e}")
            
        # Cache de tokens
        self._tokens = None
        self._token_expiry = None
        
        # Configurar logging seguro
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.info("🔐 Microsoft Auth Unificado iniciado")
    
    def mask_token(self, token: str) -> str:
        """Mascara token para logs seguros - NUNCA expor token completo"""
        if not token or len(token) < 10:
            return "***VAZIO***"
        return f"{token[:6]}...{token[-4:]}"
    
    def _encrypt_data(self, data: str) -> str:
        """Criptografa dados com Fernet - OBRIGATÓRIO para persistência"""
        try:
            encrypted = self.fernet.encrypt(data.encode()).decode()
            self.logger.debug(f"🔐 Dados criptografados: {len(encrypted)} chars")
            return encrypted
        except Exception as e:
            self.logger.error(f"❌ Erro na criptografia: {e}")
            raise
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Descriptografa dados com Fernet"""
        try:
            decrypted = self.fernet.decrypt(encrypted_data.encode()).decode()
            self.logger.debug(f"🔓 Dados descriptografados: {self.mask_token(decrypted)}")
            return decrypted
        except Exception as e:
            self.logger.error(f"❌ Erro na descriptografia: {e}")
            raise
    
    def _get_shared_token_url(self) -> str:
        """Constrói URL para acessar token compartilhado na pasta Alerta"""
        return f"https://graph.microsoft.com/v1.0/me/drive/items/{self.alerta_folder_id}:/{self.shared_token_filename}:/content"
    
    def _load_from_onedrive_shared(self) -> Optional[Dict[str, Any]]:
        """Carrega token compartilhado da pasta Alerta no OneDrive"""
        try:
            # CORREÇÃO RÁPIDA: Tentar usar qualquer token disponível nas env vars primeiro
            access_token = os.getenv("MICROSOFT_ACCESS_TOKEN") or (self._tokens and self._tokens.get("access_token"))
            
            if not access_token:
                self.logger.warning("⚠️  Sem access_token para acessar OneDrive")
                return None
                
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            url = self._get_shared_token_url()
            self.logger.info(f"📥 Carregando token compartilhado da pasta Alerta...")
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                self.logger.info(f"✅ Token carregado do OneDrive Alerta: {self.mask_token(token_data.get('refresh_token', ''))}")
                return token_data
            elif response.status_code == 404:
                self.logger.info("📄 Arquivo token.json não existe na pasta Alerta ainda")
                return None
            else:
                self.logger.warning(f"⚠️  Erro ao carregar do OneDrive Alerta: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao acessar OneDrive Alerta: {e}")
            return None
    
    def _save_to_onedrive_shared(self, token_data: Dict[str, Any]) -> bool:
        """Salva token compartilhado na pasta Alerta no OneDrive"""
        try:
            # CORREÇÃO RÁPIDA: Tentar usar qualquer token disponível
            access_token = os.getenv("MICROSOFT_ACCESS_TOKEN") or (self._tokens and self._tokens.get("access_token"))
            
            if not access_token:
                self.logger.error("❌ Sem access_token para salvar no OneDrive")
                return False
                
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # SEMPRE criptografar dados antes de salvar
            encrypted_data = {
                "access_token": self._encrypt_data(token_data["access_token"]),
                "refresh_token": self._encrypt_data(token_data["refresh_token"]),
                "expires_on": token_data.get("expires_on"),
                "encrypted": True,
                "updated_at": datetime.now().isoformat(),
                "updated_by": os.getenv("RENDER_SERVICE_NAME", "Unknown")
            }
            
            url = self._get_shared_token_url()
            self.logger.info(f"💾 Salvando token na pasta Alerta compartilhada...")
            
            response = requests.put(
                url, 
                headers=headers, 
                data=json.dumps(encrypted_data),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                self.logger.info(f"✅ Token salvo no OneDrive Alerta: {self.mask_token(token_data['refresh_token'])}")
                return True
            else:
                self.logger.error(f"❌ Erro ao salvar no OneDrive Alerta: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar no OneDrive Alerta: {e}")
            return False
    
    def _load_from_env_vars(self) -> Optional[Dict[str, Any]]:
        """Carrega tokens das environment variables (criptografados)"""
        access_token_env = os.getenv("MICROSOFT_ACCESS_TOKEN_SECURE")
        refresh_token_env = os.getenv("MICROSOFT_REFRESH_TOKEN_SECURE")
        
        if access_token_env and refresh_token_env:
            try:
                tokens = {
                    "access_token": self._decrypt_data(access_token_env),
                    "refresh_token": self._decrypt_data(refresh_token_env),
                    "expires_on": int(os.getenv("MICROSOFT_TOKEN_EXPIRES", "0"))
                }
                self.logger.info(f"✅ Tokens carregados das ENV VARS: {self.mask_token(tokens['access_token'])}")
                return tokens
            except Exception as e:
                self.logger.error(f"❌ Erro ao descriptografar tokens das ENV: {e}")
        return None
    
    def _load_from_local_fallback(self) -> Optional[Dict[str, Any]]:
        """Carrega tokens do arquivo local de fallback (contingência)"""
        try:
            if os.path.exists(self.local_fallback_path):
                with open(self.local_fallback_path, 'r') as f:
                    data = json.load(f)
                
                # Auto-migração: descriptografar se necessário
                if data.get("encrypted"):
                    data["access_token"] = self._decrypt_data(data["access_token"])
                    data["refresh_token"] = self._decrypt_data(data["refresh_token"])
                else:
                    # Token legado em texto puro - criptografar automaticamente
                    self.logger.warning("⚠️  Token local em texto puro detectado - migrando para criptografado")
                    self._save_to_local_fallback(data)
                
                self.logger.info(f"✅ Token carregado do fallback local: {self.mask_token(data.get('refresh_token', ''))}")
                return data
            return None
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar fallback local: {e}")
            return None
    
    def _save_to_local_fallback(self, token_data: Dict[str, Any]):
        """Salva tokens no arquivo local de fallback (sempre criptografado)"""
        try:
            encrypted_data = {
                "access_token": self._encrypt_data(token_data["access_token"]),
                "refresh_token": self._encrypt_data(token_data["refresh_token"]),
                "expires_on": token_data.get("expires_on"),
                "encrypted": True,
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.local_fallback_path, 'w') as f:
                json.dump(encrypted_data, f, indent=2)
            
            self.logger.info(f"✅ Token salvo no fallback local: {self.mask_token(token_data['refresh_token'])}")
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar fallback local: {e}")
    
    def load_tokens(self) -> bool:
        """
        CORREÇÃO RÁPIDA: Carrega tokens com bootstrap inicial
        1. Environment Variables (compatibilidade)
        2. OneDrive compartilhado (pasta Alerta) - COM BOOTSTRAP
        3. Fallback local
        """
        self.logger.info("🔍 Iniciando carregamento de tokens...")
        
        # 1. Tentar environment variables primeiro (criptografadas)
        env_tokens = self._load_from_env_vars()
        if env_tokens:
            self._tokens = env_tokens
            return True
        
        # 2. NOVO: Tentar environment variables em texto puro (bootstrap)
        access_token_plain = os.getenv("MICROSOFT_ACCESS_TOKEN")
        refresh_token_plain = os.getenv("MICROSOFT_REFRESH_TOKEN")
        
        if access_token_plain and refresh_token_plain:
            self._tokens = {
                "access_token": access_token_plain,
                "refresh_token": refresh_token_plain,
                "expires_on": int(os.getenv("MICROSOFT_TOKEN_EXPIRES", str(int(datetime.now().timestamp()) + 3600)))
            }
            self.logger.info("✅ Tokens bootstrap carregados das ENV VARS texto plano")
            
            # Tentar carregar do OneDrive e migrar automaticamente
            onedrive_tokens = self._load_from_onedrive_shared()
            if onedrive_tokens:
                # Auto-migração de token legado
                if onedrive_tokens.get("encrypted"):
                    try:
                        onedrive_tokens["access_token"] = self._decrypt_data(onedrive_tokens["access_token"])
                        onedrive_tokens["refresh_token"] = self._decrypt_data(onedrive_tokens["refresh_token"])
                        self._tokens = onedrive_tokens
                        self.logger.info("✅ Migrado para token OneDrive criptografado")
                    except Exception as e:
                        self.logger.error(f"❌ Erro ao descriptografar OneDrive: {e}")
                else:
                    # Token legado em texto puro - usar e criptografar
                    self._tokens = onedrive_tokens
                    self.logger.warning("⚠️  Token OneDrive em texto puro detectado - usando e migrando...")
                    # Auto-salvar criptografado
                    self.save_tokens(onedrive_tokens["access_token"], onedrive_tokens["refresh_token"])
            
            return True
        
        # 3. Tentar OneDrive compartilhado diretamente
        onedrive_tokens = self._load_from_onedrive_shared()
        if onedrive_tokens:
            if onedrive_tokens.get("encrypted"):
                try:
                    onedrive_tokens["access_token"] = self._decrypt_data(onedrive_tokens["access_token"])
                    onedrive_tokens["refresh_token"] = self._decrypt_data(onedrive_tokens["refresh_token"])
                except Exception as e:
                    self.logger.error(f"❌ Erro ao descriptografar OneDrive: {e}")
                    onedrive_tokens = None
                    
            if onedrive_tokens:
                self._tokens = onedrive_tokens
                return True
        
        # 4. Fallback local
        local_tokens = self._load_from_local_fallback()
        if local_tokens:
            self._tokens = local_tokens
            return True
        
        self.logger.warning("⚠️  Nenhum token encontrado em nenhuma fonte")
        return False
    
    def save_tokens(self, access_token: str, refresh_token: str, expires_in: int = 3600):
        """Salva tokens de forma segura (OneDrive Alerta + fallback local)"""
        expires_on = int(datetime.now().timestamp()) + expires_in
        
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_on": expires_on
        }
        
        # Atualizar cache
        self._tokens = token_data.copy()
        self._token_expiry = datetime.fromtimestamp(expires_on)
        
        self.logger.info(f"💾 Salvando tokens: {self.mask_token(refresh_token)}")
        
        # Salvar no OneDrive Alerta (prioridade)
        onedrive_saved = self._save_to_onedrive_shared(token_data)
        
        # Sempre salvar fallback local
        self._save_to_local_fallback(token_data)
        
        if onedrive_saved:
            self.logger.info("✅ Tokens salvos com sucesso (OneDrive Alerta + local)")
        else:
            self.logger.warning("⚠️  OneDrive Alerta falhou, mas fallback local OK")
    
    def is_token_valid(self) -> bool:
        """Verifica se o token ainda é válido (com buffer de 5 minutos)"""
        if not self._tokens:
            return False
            
        if not self._token_expiry:
            expires_on = self._tokens.get("expires_on")
            if expires_on:
                self._token_expiry = datetime.fromtimestamp(expires_on)
            else:
                return False
        
        # Buffer de 5 minutos para renovação
        valid_until = self._token_expiry - timedelta(minutes=5)
        is_valid = datetime.now() < valid_until
        
        if not is_valid:
            self.logger.info("⏰ Token próximo do vencimento - renovação necessária")
        
        return is_valid
    
    def refresh_access_token(self) -> bool:
        """Renova o access token usando refresh token"""
        if not self._tokens or not self._tokens.get("refresh_token"):
            self.logger.error("❌ Refresh token não disponível")
            return False
        
        self.logger.info(f"🔄 Renovando token: {self.mask_token(self._tokens['refresh_token'])}")
        
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': self._tokens["refresh_token"]
            }
            
            response = requests.post(
                f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token',
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                token_response = response.json()
                
                # Salvar novos tokens
                self.save_tokens(
                    token_response['access_token'],
                    token_response.get('refresh_token', self._tokens["refresh_token"]),
                    token_response.get('expires_in', 3600)
                )
                
                self.logger.info(f"✅ Token renovado com sucesso: {self.mask_token(token_response['access_token'])}")
                return True
            else:
                self.logger.error(f"❌ Erro na renovação: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro na renovação: {e}")
            return False
    
    @property
    def access_token(self) -> Optional[str]:
        """Retorna access token válido (renova automaticamente se necessário)"""
        if not self._tokens:
            if not self.load_tokens():
                self.logger.error("❌ Nenhum token disponível")
                return None
        
        if not self.is_token_valid():
            if not self.refresh_access_token():
                self.logger.error("❌ Falha na renovação do token")
                return None
        
        return self._tokens.get("access_token")
    
    @property
    def refresh_token(self) -> Optional[str]:
        """Retorna refresh token"""
        if not self._tokens:
            if not self.load_tokens():
                return None
        return self._tokens.get("refresh_token")
    
    def debug_status(self):
        """Debug information com logs seguros"""
        self.logger.info("🔧 Microsoft Auth Unificado - Status de Debug:")
        self.logger.info(f"   Client ID: {self.mask_token(self.client_id)}")
        self.logger.info(f"   Alerta Folder ID: {self.mask_token(self.alerta_folder_id)}")
        self.logger.info(f"   Access Token: {'✅ disponível' if self._tokens and self._tokens.get('access_token') else '❌ não disponível'}")
        self.logger.info(f"   Refresh Token: {'✅ disponível' if self._tokens and self._tokens.get('refresh_token') else '❌ não disponível'}")
        self.logger.info(f"   Token válido: {'✅ sim' if self.is_token_valid() else '❌ não'}")

# Função utilitária para gerar chave de criptografia
def generate_encryption_key() -> str:
    """Gera nova chave Fernet para environment variable"""
    return Fernet.generate_key().decode()

# Compatibilidade com código existente da BRK e CCB Alerta
class MicrosoftAuth(MicrosoftAuthUnified):
    """Classe de compatibilidade para manter funcionamento do código BRK e CCB Alerta existente"""
    
    def obter_headers_autenticados(self) -> dict:
        """Método de compatibilidade para código BRK/CCB existente"""
        token = self.access_token
        if not token:
            raise Exception("Token de acesso não disponível")
        
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def get_microsoft_token(self) -> dict:
        """Método de compatibilidade para retornar token no formato esperado (BRK)"""
        if not self._tokens:
            if not self.load_tokens():
                return {}
        
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_on': self._tokens.get('expires_on', 0) if self._tokens else 0
        }
    
    # === MÉTODOS DE COMPATIBILIDADE CCB ALERTA ===
    
    def carregar_token(self) -> bool:
        """Método de compatibilidade CCB Alerta - Carrega token"""
        return self.load_tokens()
    
    def salvar_token_persistent(self, access_token: str, refresh_token: str, expires_in: int = 3600):
        """Método de compatibilidade CCB Alerta - Salva token de forma persistente"""
        self.save_tokens(access_token, refresh_token, expires_in)
        self.logger.info("✅ Token salvo com persistência (CCB Alerta compatible)")
    
    def atualizar_token(self) -> bool:
        """Método de compatibilidade CCB Alerta - Atualiza/renova token"""
        success = self.refresh_access_token()
        if success:
            self.logger.info("✅ Token atualizado com sucesso (CCB Alerta compatible)")
        else:
            self.logger.error("❌ Falha ao atualizar token (CCB Alerta compatible)")
        return success
    
    def validar_token(self) -> bool:
        """Método de compatibilidade CCB Alerta - Valida token"""
        valid = self.is_token_valid()
        if valid:
            self.logger.info("✅ Token válido (CCB Alerta compatible)")
        else:
            self.logger.warning("⚠️ Token inválido ou expirado (CCB Alerta compatible)")
        return valid
    
    def status_autenticacao(self) -> dict:
        """Método de compatibilidade CCB Alerta - Status da autenticação"""
        if not self._tokens:
            self.load_tokens()
            
        return {
            'autenticado': bool(self._tokens and self._tokens.get('access_token')),
            'token_valido': self.is_token_valid() if self._tokens else False,
            'access_token': self.mask_token(self._tokens.get('access_token', '')) if self._tokens else None,
            'refresh_token': self.mask_token(self._tokens.get('refresh_token', '')) if self._tokens else None,
            'expires_on': self._tokens.get('expires_on', 0) if self._tokens else 0
        }
    
    # === MÉTODOS DE COMPATIBILIDADE ENEL ===
    
    def testar_acesso_pasta_enel(self) -> bool:
        """Método de compatibilidade Enel - Testa acesso à pasta Enel"""
        try:
            pasta_enel_id = os.getenv("ONEDRIVE_ENEL_ID")
            if not pasta_enel_id:
                self.logger.error("❌ ONEDRIVE_ENEL_ID não configurado")
                return False
                
            token = self.access_token
            if not token:
                self.logger.error("❌ Token não disponível para teste")
                return False
                
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Testar acesso à pasta Enel
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_enel_id}"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                pasta_info = response.json()
                self.logger.info(f"✅ Acesso à pasta Enel OK: {pasta_info.get('name', 'Enel')}")
                return True
            else:
                self.logger.error(f"❌ Erro ao acessar pasta Enel: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro no teste da pasta Enel: {e}")
            return False

if __name__ == "__main__":
    # Utilitário para gerar chave de criptografia
    print("🔑 Gerador de chave de criptografia Fernet:")
    print(f"ENCRYPTION_KEY={generate_encryption_key()}")
    print("\n📋 Configure esta chave nas Environment Variables de todos os Renders:")
    print("   - BRK: ENCRYPTION_KEY=<chave_gerada>")
    print("   - CCB Alerta: ENCRYPTION_KEY=<chave_gerada>")
    print("   - Enel: ENCRYPTION_KEY=<chave_gerada>")
