#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: processor/onedrive_manager.py
💾 FUNÇÃO: Gerenciador de estrutura OneDrive ENEL
🔧 DESCRIÇÃO: Criar e gerenciar pastas no OneDrive para ENEL
👨‍💼 AUTOR: Baseado na lógica BRK adaptada para ENEL
🔒 ESTRUTURA: /ENEL/Faturas/YYYY/MM/ + /ENEL/Planilhas/
"""

import os
import requests
from datetime import datetime
from typing import Dict, Optional

class OneDriveManagerEnel:
    """
    Gerenciador de estrutura OneDrive para ENEL
    
    Responsabilidades:
    - Criar pasta raiz /ENEL/ no OneDrive
    - Criar subpastas organizacionais
    - Gerenciar estrutura de pastas por ano/mês
    - Upload de arquivos para pastas corretas
    """
    
    def __init__(self, auth_manager):
        """
        Inicializar gerenciador OneDrive ENEL
        
        Args:
            auth_manager: Instância do MicrosoftAuth
        """
        self.auth = auth_manager
        
        # IDs das pastas (corrigido para usar variáveis do Render ENEL)
        self.pasta_enel_id = os.getenv('ONEDRIVE_ENEL_ID')  # Pasta raiz ENEL
        
        # IDs dinâmicos (serão criados/descobertos via API)
        self._pasta_faturas_id = None
        self._pasta_planilhas_id = None
        self._pasta_ano_atual_id = None
        self._pastas_meses_cache = {}
        
        print(f"OneDrive Manager ENEL inicializado")
        print(f"Pasta ENEL ID: {self.pasta_enel_id[:10] + '...' if self.pasta_enel_id else 'NAO CONFIGURADO'}")
        print(f"Estrutura sera criada dinamicamente via API")
    
    def garantir_estrutura_completa(self) -> bool:
        """
        Criar estrutura OneDrive ENEL via API Microsoft Graph (IGUAL BRK)
        
        Cria:
        - /ENEL/2025/
        - /ENEL/2025/08|09|10/
        (faturas renomeadas + planilhas na mesma pasta por mês)
        
        Returns:
            bool: True se estrutura foi criada com sucesso
        """
        try:
            print(f"Criando estrutura OneDrive ENEL via API...")
            
            # Verificar se temos pasta ENEL configurada
            if not self.pasta_enel_id:
                print(f"ERRO: ONEDRIVE_ENEL_ID nao configurado no Render")
                return False
            
            if not self.auth.access_token:
                print(f"ERRO: Token de acesso nao disponivel")
                return False
            
            print(f"SUCCESS: Pasta ENEL: {self.pasta_enel_id[:10]}...")
            
            headers = {
                'Authorization': f'Bearer {self.auth.access_token}',
                'Content-Type': 'application/json'
            }
            
            # 1. Criar pasta do ano direto na raiz (IGUAL BRK)
            ano_atual = datetime.now().year
            pasta_ano_id = self._criar_pasta(str(ano_atual), self.pasta_enel_id, headers)
            if not pasta_ano_id:
                return False
            self._pasta_ano_atual_id = pasta_ano_id
            
            # 2. Criar pastas dos meses direto no ano (IGUAL BRK)
            meses = ["08", "09", "10"]
            meses_criados = 0
            
            for mes in meses:
                pasta_mes_id = self._criar_pasta(mes, pasta_ano_id, headers)
                if pasta_mes_id:
                    self._pastas_meses_cache[f"{ano_atual}-{mes}"] = pasta_mes_id
                    meses_criados += 1
                    
                    # Criar arquivo README no mês explicando estrutura
                    self._criar_readme_mes(pasta_mes_id, mes, headers)
            
            print(f"SUCCESS: Estrutura ENEL criada estilo BRK: {meses_criados} meses")
            print(f"ESTRUTURA: /ENEL/{ano_atual}/MM/ (faturas + planilhas juntas)")
            return meses_criados > 0
            
        except Exception as e:
            print(f"ERRO: Erro criando estrutura OneDrive ENEL: {e}")
            return False
    
    def _criar_pasta(self, nome_pasta: str, parent_id: str, headers: dict) -> Optional[str]:
        """
        Criar pasta no OneDrive ou retornar ID se já existe
        
        Args:
            nome_pasta: Nome da pasta a criar
            parent_id: ID da pasta pai
            headers: Headers de autenticação
            
        Returns:
            str: ID da pasta criada ou existente, None se erro
        """
        try:
            # Tentar criar pasta
            folder_data = {"name": nome_pasta, "folder": {}}
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{parent_id}/children"
            
            response = requests.post(url, headers=headers, json=folder_data, timeout=30)
            
            if response.status_code in [200, 201]:
                folder_info = response.json()
                pasta_id = folder_info['id']
                print(f"SUCCESS: Pasta '{nome_pasta}' criada: {pasta_id[:10]}...")
                return pasta_id
            elif response.status_code == 409:
                # Pasta já existe, buscar ID
                print(f"INFO: Pasta '{nome_pasta}' ja existe, buscando ID...")
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    children = response.json().get('value', [])
                    existing_folder = next((item for item in children if item.get('name') == nome_pasta), None)
                    if existing_folder:
                        pasta_id = existing_folder['id']
                        print(f"SUCCESS: Pasta '{nome_pasta}' encontrada: {pasta_id[:10]}...")
                        return pasta_id
                
                print(f"ERRO: Pasta '{nome_pasta}' nao encontrada apos criacao")
                return None
            else:
                print(f"ERRO: Erro criar pasta '{nome_pasta}': HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"ERRO: Erro criar pasta '{nome_pasta}': {e}")
            return None
    
    def _criar_readme_mes(self, pasta_mes_id: str, mes: str, headers: dict) -> bool:
        """
        Criar arquivo README explicando estrutura BRK no mês
        
        Args:
            pasta_mes_id: ID da pasta do mês
            mes: Número do mês (string)
            headers: Headers de autenticação
            
        Returns:
            bool: True se arquivo foi criado
        """
        try:
            ano_atual = datetime.now().year
            
            # Conteúdo do README
            conteudo = f"""PASTA ENEL - MÊS {mes}/{ano_atual}

📁 ESTRUTURA IGUAL BRK:
- Faturas ENEL renomeadas (PDF)
- Planilha de controle mensal (Excel)
- AMBOS na mesma pasta

📊 ARQUIVOS ESPERADOS:
- Faturas: DD-MM-ENEL MM-YYYY - LOCAL - vc. DD-MM-YYYY - R$ XX,XX.pdf
- Planilha: Controle_ENEL_{ano_atual}_{mes}.xlsx

🔍 ACESSO TESOURARIA:
✅ Tesouraria tem acesso total a esta pasta
✅ Pode baixar faturas e planilhas
✅ Estrutura idêntica ao sistema BRK

Data criação: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Sistema: ENEL Web Render
"""
            
            nome_arquivo = f"README_ENEL_{ano_atual}_{mes}.txt"
            upload_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_mes_id}:/{nome_arquivo}:/content"
            
            file_headers = {
                'Authorization': f'Bearer {self.auth.access_token}',
                'Content-Type': 'text/plain'
            }
            
            response = requests.put(
                upload_url,
                headers=file_headers,
                data=conteudo.encode('utf-8'),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                print(f"SUCCESS: README {mes}/{ano_atual} criado (estrutura BRK)")
                return True
            else:
                print(f"ERRO: Erro criar README {mes}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"ERRO: Erro criar README {mes}: {e}")
            return False
    
    def obter_ids_estrutura(self) -> Dict:
        """
        Obter IDs da estrutura criada
        
        Returns:
            Dict: IDs das pastas principais
        """
        return {
            "pasta_enel": self.pasta_enel_id,
            "pasta_faturas": self._pasta_faturas_id,
            "pasta_planilhas": self._pasta_planilhas_id or "nao_implementado"
        }
    
    
    def garantir_pasta_mes_ano(self, ano: int, mes: int) -> Optional[str]:
        """
        Garantir estrutura /ENEL/Faturas/YYYY/MM/ para um mês específico
        
        Args:
            ano (int): Ano da fatura (ex: 2024)
            mes (int): Mês da fatura (ex: 12)
            
        Returns:
            str: ID da pasta do mês ou None se erro
        """
        try:
            if not self.pasta_faturas_id:
                print(f"❌ Pasta Faturas não configurada (variável ONEDRIVE_PASTA_FATURAS_ENEL_ID)")
                return None
            
            headers = self.auth.obter_headers_autenticados()
            
            # 1. Verificar/criar pasta do ano
            ano_str = str(ano)
            pasta_ano_id = self._verificar_pasta_existe(self.pasta_faturas_id, ano_str, headers)
            if not pasta_ano_id:
                pasta_ano_id = self._criar_pasta_onedrive(self.pasta_faturas_id, ano_str, headers)
            
            if not pasta_ano_id:
                print(f"❌ Falha criando pasta ano /{ano_str}/")
                return None
            
            # 2. Verificar/criar pasta do mês
            mes_str = f"{mes:02d}"  # 01, 02, 03, etc.
            pasta_mes_id = self._verificar_pasta_existe(pasta_ano_id, mes_str, headers)
            if not pasta_mes_id:
                pasta_mes_id = self._criar_pasta_onedrive(pasta_ano_id, mes_str, headers)
            
            if pasta_mes_id:
                print(f"✅ Pasta /ENEL/Faturas/{ano_str}/{mes_str}/ pronta")
                return pasta_mes_id
            else:
                print(f"❌ Falha criando pasta mês /{mes_str}/")
                return None
                
        except Exception as e:
            print(f"❌ Erro garantindo pasta {ano}/{mes:02d}: {e}")
            return None
    
    def _verificar_pasta_existe(self, pasta_pai_id: str, nome_pasta: str, headers) -> Optional[str]:
        """
        Verificar se uma pasta já existe
        
        Args:
            pasta_pai_id (str): ID da pasta pai
            nome_pasta (str): Nome da pasta a verificar
            headers (dict): Headers autenticados
            
        Returns:
            str: ID da pasta se existe, None se não existe
        """
        try:
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_pai_id}/children"
            params = {"$filter": f"name eq '{nome_pasta}' and folder ne null"}
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('value', [])
                
                if items:
                    return items[0]['id']
                else:
                    return None
            else:
                print(f"⚠️ Erro verificando pasta {nome_pasta}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro verificando pasta {nome_pasta}: {e}")
            return None
    
    def _criar_pasta_onedrive(self, pasta_pai_id: str, nome_pasta: str, headers) -> Optional[str]:
        """
        Criar pasta no OneDrive via Microsoft Graph API
        
        Args:
            pasta_pai_id (str): ID da pasta pai
            nome_pasta (str): Nome da nova pasta
            headers (dict): Headers autenticados
            
        Returns:
            str: ID da nova pasta ou None se erro
        """
        try:
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_pai_id}/children"
            
            data = {
                "name": nome_pasta,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename"  # Renomeia se já existir
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 201:
                nova_pasta = response.json()
                pasta_id = nova_pasta['id']
                print(f"📁 Pasta criada: {nome_pasta} (ID: {pasta_id[:10]}...)")
                return pasta_id
            else:
                print(f"❌ Erro criando pasta {nome_pasta}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro criando pasta {nome_pasta}: {e}")
            return None
    
    def upload_arquivo(self, arquivo_bytes: bytes, nome_arquivo: str, pasta_id: str) -> bool:
        """
        Upload de arquivo para pasta específica no OneDrive
        
        Args:
            arquivo_bytes (bytes): Conteúdo do arquivo
            nome_arquivo (str): Nome do arquivo
            pasta_id (str): ID da pasta destino
            
        Returns:
            bool: True se upload bem-sucedido
        """
        try:
            if not self.auth.access_token:
                return False
            
            headers = self.auth.obter_headers_autenticados()
            
            # Upload simples para arquivos pequenos (< 4MB)
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_id}:/{nome_arquivo}:/content"
            
            # Headers específicos para upload
            upload_headers = {
                'Authorization': headers['Authorization'],
                'Content-Type': 'application/octet-stream'
            }
            
            response = requests.put(url, headers=upload_headers, data=arquivo_bytes, timeout=60)
            
            if response.status_code in [200, 201]:
                print(f"📤 Upload realizado: {nome_arquivo}")
                return True
            else:
                print(f"❌ Erro upload {nome_arquivo}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro upload {nome_arquivo}: {e}")
            return False
    
    
    def testar_conectividade(self) -> Dict:
        """
        Testar conectividade e estrutura OneDrive
        
        Returns:
            Dict: Status da conectividade
        """
        try:
            if not self.auth.access_token:
                return {
                    "sucesso": False,
                    "erro": "Token não disponível"
                }
            
            headers = self.auth.obter_headers_autenticados()
            
            # Teste básico - obter informações do drive
            url = "https://graph.microsoft.com/v1.0/me/drive"
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                drive_info = response.json()
                
                return {
                    "sucesso": True,
                    "drive_id": drive_info.get('id', 'N/A'),
                    "drive_type": drive_info.get('driveType', 'N/A'),
                    "owner": drive_info.get('owner', {}).get('user', {}).get('displayName', 'N/A'),
                    "quota_total": drive_info.get('quota', {}).get('total', 0),
                    "quota_usado": drive_info.get('quota', {}).get('used', 0),
                    "estrutura_enel": {
                        "pasta_enel": bool(self.pasta_enel_id),
                        "pasta_faturas": bool(self.pasta_faturas_id),
                        "pasta_planilhas": bool(self.pasta_planilhas_id)
                    }
                }
            else:
                return {
                    "sucesso": False,
                    "erro": f"Erro acessando drive: HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro testando conectividade: {str(e)}"
            }
    
    def baixar_pdf_fatura(self, nome_arquivo: str) -> Optional[bytes]:
        """
        Baixar PDF de fatura da estrutura OneDrive ENEL
        
        Busca em /ENEL/Faturas/YYYY/MM/ pelo arquivo especificado
        
        Args:
            nome_arquivo (str): Nome do arquivo PDF a baixar
            
        Returns:
            bytes: Conteúdo do PDF ou None se não encontrado
        """
        try:
            if not self.auth.access_token:
                print(f"❌ Token não disponível para download")
                return None
            
            if not nome_arquivo:
                print(f"❌ Nome do arquivo não fornecido")
                return None
            
            print(f"📥 Buscando PDF: {nome_arquivo}")
            
            headers = self.auth.obter_headers_autenticados()
            
            # Buscar nas pastas de faturas (ano/mês atual e anteriores)
            anos_busca = [datetime.now().year, datetime.now().year - 1]  # Ano atual e anterior
            
            for ano in anos_busca:
                for mes in range(1, 13):
                    try:
                        # Construir caminho da pasta
                        pasta_mes_path = f"/ENEL/Faturas/{ano}/{mes:02d}"
                        
                        # Buscar pasta do mês
                        url_busca = f"https://graph.microsoft.com/v1.0/me/drive/root:{pasta_mes_path}:/children"
                        response = requests.get(url_busca, headers=headers, timeout=15)
                        
                        if response.status_code != 200:
                            continue  # Pasta não existe, tentar próxima
                        
                        arquivos = response.json().get('value', [])
                        
                        # Procurar arquivo específico
                        for arquivo in arquivos:
                            arquivo_nome = arquivo.get('name', '')
                            
                            # Match exato ou contém o nome
                            if (arquivo_nome == nome_arquivo or 
                                nome_arquivo in arquivo_nome or
                                arquivo_nome.replace('.pdf', '') in nome_arquivo):
                                
                                print(f"📍 PDF encontrado: {pasta_mes_path}/{arquivo_nome}")
                                
                                # Baixar o arquivo
                                download_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{arquivo['id']}/content"
                                download_response = requests.get(download_url, headers=headers, timeout=60)
                                
                                if download_response.status_code == 200:
                                    pdf_bytes = download_response.content
                                    print(f"✅ PDF baixado: {len(pdf_bytes)} bytes")
                                    return pdf_bytes
                                else:
                                    print(f"❌ Erro baixando PDF: HTTP {download_response.status_code}")
                                    continue
                        
                    except Exception as e:
                        print(f"⚠️ Erro buscando em {ano}/{mes:02d}: {e}")
                        continue
            
            # Se não encontrou, tentar busca geral na pasta raiz de faturas
            try:
                print(f"🔍 Buscando em pasta raiz de faturas...")
                
                if self.pasta_faturas_id:
                    url_busca = f"https://graph.microsoft.com/v1.0/me/drive/items/{self.pasta_faturas_id}/children"
                    response = requests.get(url_busca, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        arquivos = response.json().get('value', [])
                        
                        for arquivo in arquivos:
                            arquivo_nome = arquivo.get('name', '')
                            
                            if (arquivo_nome == nome_arquivo or nome_arquivo in arquivo_nome):
                                print(f"📍 PDF encontrado na pasta raiz: {arquivo_nome}")
                                
                                # Baixar o arquivo
                                download_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{arquivo['id']}/content"
                                download_response = requests.get(download_url, headers=headers, timeout=60)
                                
                                if download_response.status_code == 200:
                                    pdf_bytes = download_response.content
                                    print(f"✅ PDF baixado da raiz: {len(pdf_bytes)} bytes")
                                    return pdf_bytes
            
            except Exception as e:
                print(f"⚠️ Erro na busca geral: {e}")
            
            print(f"❌ PDF não encontrado: {nome_arquivo}")
            return None
            
        except Exception as e:
            print(f"❌ Erro baixando PDF {nome_arquivo}: {e}")
            return None
    
    def listar_pdfs_disponiveis(self, pasta_mes: str = None) -> list:
        """
        Listar PDFs disponíveis na estrutura ENEL
        
        Args:
            pasta_mes (str): Pasta específica no formato "YYYY/MM" (opcional)
            
        Returns:
            list: Lista de dicionários com info dos PDFs
        """
        try:
            if not self.auth.access_token:
                return []
            
            headers = self.auth.obter_headers_autenticados()
            pdfs_encontrados = []
            
            if pasta_mes:
                # Buscar em pasta específica
                pasta_path = f"/ENEL/Faturas/{pasta_mes}"
                url_busca = f"https://graph.microsoft.com/v1.0/me/drive/root:{pasta_path}:/children"
                
                try:
                    response = requests.get(url_busca, headers=headers, timeout=15)
                    if response.status_code == 200:
                        arquivos = response.json().get('value', [])
                        
                        for arquivo in arquivos:
                            if arquivo.get('name', '').lower().endswith('.pdf'):
                                pdfs_encontrados.append({
                                    'nome': arquivo['name'],
                                    'id': arquivo['id'],
                                    'tamanho': arquivo.get('size', 0),
                                    'pasta': pasta_mes,
                                    'modificado': arquivo.get('lastModifiedDateTime', '')
                                })
                except:
                    pass
            else:
                # Buscar em todas as pastas do ano atual
                ano_atual = datetime.now().year
                
                for mes in range(1, 13):
                    pasta_path = f"/ENEL/Faturas/{ano_atual}/{mes:02d}"
                    url_busca = f"https://graph.microsoft.com/v1.0/me/drive/root:{pasta_path}:/children"
                    
                    try:
                        response = requests.get(url_busca, headers=headers, timeout=15)
                        if response.status_code == 200:
                            arquivos = response.json().get('value', [])
                            
                            for arquivo in arquivos:
                                if arquivo.get('name', '').lower().endswith('.pdf'):
                                    pdfs_encontrados.append({
                                        'nome': arquivo['name'],
                                        'id': arquivo['id'],
                                        'tamanho': arquivo.get('size', 0),
                                        'pasta': f"{ano_atual}/{mes:02d}",
                                        'modificado': arquivo.get('lastModifiedDateTime', '')
                                    })
                    except:
                        continue
            
            print(f"📋 PDFs encontrados: {len(pdfs_encontrados)}")
            return pdfs_encontrados
            
        except Exception as e:
            print(f"❌ Erro listando PDFs: {e}")
            return []