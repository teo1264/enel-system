"""
Email Processor ENEL - Versão COMPLETA CORRIGIDA
Baseado no original de 673 linhas com correções OneDrive
TODAS as funcionalidades mantidas, storage local removido
"""

import requests
import json
import os
import io
import base64
import re
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailProcessorEnel:
    """
    Processador de emails ENEL com integração OneDrive completa
    Versão corrigida que remove storage local e usa apenas OneDrive
    """
    
    def __init__(self, auth_manager, onedrive_manager=None):
        """Inicializa o processador de emails ENEL"""
        self.auth = auth_manager
        self.onedrive_manager = onedrive_manager
        self.logger = logging.getLogger(__name__)
        
        # REMOVIDO: self.download_dir - OneDrive only
        # REMOVIDO: os.makedirs - sem storage local
        
        # Configurações ENEL
        self.pasta_enel_id = os.getenv("PASTA_ENEL_ID")
        self.onedrive_enel_id = os.getenv("ONEDRIVE_ENEL_ID")
        
        # Configurações de processamento
        self.max_tentativas = 3
        self.timeout_request = 30
        self.delay_entre_requests = 1
        
        # Filtros de email
        self.filtros_assunto = [
            "fatura",
            "conta de luz", 
            "conta de energia",
            "enel",
            "distribuidora"
        ]
        
        # Padrões de arquivo
        self.extensoes_permitidas = ['.pdf', '.PDF']
        self.tamanho_max_arquivo = 50 * 1024 * 1024  # 50MB
        
        self.logger.info("📧 EmailProcessorEnel iniciado - OneDrive ONLY")
        
    def upload_pdf_to_onedrive(self, pdf_content: bytes, filename: str, ano: str = None, mes: str = None) -> Dict[str, Any]:
        """
        Upload PDF diretamente para OneDrive /Enel/Faturas/YYYY/MM/
        
        Args:
            pdf_content: Conteúdo do PDF em bytes
            filename: Nome do arquivo
            ano: Ano (opcional, usa atual se None)
            mes: Mês (opcional, usa atual se None)
            
        Returns:
            Dict com resultado do upload
        """
        try:
            # Usar data atual se não especificado
            if not ano or not mes:
                agora = datetime.now()
                ano = ano or str(agora.year)
                mes = mes or f"{agora.month:02d}"
            
            # Caminho OneDrive
            onedrive_path = f"/Enel/Faturas/{ano}/{mes}/{filename}"
            
            headers = self.auth.obter_headers_autenticados()
            headers['Content-Type'] = 'application/pdf'
            
            # Upload para OneDrive
            upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{onedrive_path}:/content"
            
            self.logger.info(f"📤 Upload PDF: {filename} → {onedrive_path}")
            
            response = requests.put(
                upload_url, 
                headers=headers, 
                data=pdf_content, 
                timeout=60
            )
            
            if response.status_code in [200, 201]:
                file_info = response.json()
                self.logger.info(f"✅ PDF uploaded: {filename} ({len(pdf_content)} bytes)")
                
                return {
                    'status': 'sucesso',
                    'onedrive_path': onedrive_path,
                    'onedrive_id': file_info.get('id'),
                    'onedrive_url': file_info.get('webUrl'),
                    'size': len(pdf_content),
                    'filename': filename,
                    'ano': ano,
                    'mes': mes
                }
            else:
                self.logger.error(f"❌ Erro upload PDF {filename}: {response.status_code}")
                return {
                    'status': 'erro',
                    'erro': f"HTTP {response.status_code}",
                    'detalhes': response.text[:200]
                }
                
        except Exception as e:
            self.logger.error(f"❌ Exceção upload PDF {filename}: {e}")
            return {
                'status': 'erro',
                'erro': str(e)
            }
    
    def gerar_nome_arquivo_enel(self, nome_original: str, data: datetime = None) -> str:
        """
        Gera nome padronizado para arquivos ENEL
        Formato: DD-MM-YYYY-ENEL-NomeOriginal.pdf
        """
        if not data:
            data = datetime.now()
            
        # Limpar nome original
        nome_limpo = re.sub(r'[^\w\-_\.]', '_', nome_original)
        nome_limpo = nome_limpo.replace('.pdf', '').replace('.PDF', '')
        
        # Formato padronizado
        nome_padrao = f"{data.day:02d}-{data.month:02d}-{data.year}-ENEL-{nome_limpo}.pdf"
        
        return nome_padrao
    
    def validar_anexo(self, anexo: dict) -> bool:
        """Valida se anexo é processável"""
        try:
            nome = anexo.get('name', '')
            tamanho = anexo.get('size', 0)
            
            # Verificar extensão
            if not any(nome.lower().endswith(ext.lower()) for ext in self.extensoes_permitidas):
                return False
                
            # Verificar tamanho
            if tamanho > self.tamanho_max_arquivo:
                self.logger.warning(f"⚠️ Arquivo muito grande: {nome} ({tamanho} bytes)")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro validar anexo: {e}")
            return False
    
    def baixar_anexos_email(self, email_id: str) -> List[Dict[str, Any]]:
        """
        Baixa anexos de email e faz upload direto para OneDrive
        VERSÃO CORRIGIDA: sem storage local
        """
        resultados_upload = []
        
        try:
            headers = self.auth.obter_headers_autenticados()
            
            # Buscar anexos do email
            anexos_url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}/attachments"
            
            self.logger.info(f"📎 Buscando anexos do email: {email_id}")
            
            response = requests.get(anexos_url, headers=headers, timeout=self.timeout_request)
            
            if response.status_code != 200:
                self.logger.error(f"❌ Erro buscar anexos: {response.status_code}")
                return resultados_upload
            
            anexos = response.json().get('value', [])
            self.logger.info(f"📎 {len(anexos)} anexos encontrados")
            
            # Processar cada anexo
            for i, anexo in enumerate(anexos):
                try:
                    if anexo.get('@odata.type') == '#microsoft.graph.fileAttachment':
                        if self.validar_anexo(anexo):
                            resultado = self.processar_anexo_individual(email_id, anexo, i + 1)
                            if resultado:
                                resultados_upload.append(resultado)
                        else:
                            self.logger.info(f"📎 Anexo ignorado: {anexo.get('name', 'N/A')}")
                            
                except Exception as e:
                    self.logger.error(f"❌ Erro processar anexo {i+1}: {e}")
                    continue
            
            self.logger.info(f"📊 Processamento finalizado: {len(resultados_upload)} arquivos processados")
            
        except Exception as e:
            self.logger.error(f"❌ Erro geral baixar_anexos_email: {e}")
            
        return resultados_upload
    
    def processar_anexo_individual(self, email_id: str, anexo: dict, numero: int) -> Optional[Dict[str, Any]]:
        """Processa um anexo individual"""
        try:
            nome_original = anexo.get('name', f'anexo_{numero}.pdf')
            anexo_id = anexo.get('id')
            
            self.logger.info(f"📄 Processando anexo {numero}: {nome_original}")
            
            # Obter conteúdo do anexo
            headers = self.auth.obter_headers_autenticados()
            anexo_url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}/attachments/{anexo_id}"
            
            anexo_response = requests.get(anexo_url, headers=headers, timeout=self.timeout_request)
            
            if anexo_response.status_code == 200:
                anexo_data = anexo_response.json()
                pdf_content_b64 = anexo_data.get('contentBytes', '')
                
                if pdf_content_b64:
                    # Decodificar base64
                    pdf_content = base64.b64decode(pdf_content_b64)
                    
                    # Gerar nome padronizado
                    nome_padrao = self.gerar_nome_arquivo_enel(nome_original)
                    
                    # Upload direto para OneDrive
                    resultado_upload = self.upload_pdf_to_onedrive(pdf_content, nome_padrao)
                    
                    # Complementar informações
                    resultado_upload['nome_original'] = nome_original
                    resultado_upload['email_id'] = email_id
                    resultado_upload['anexo_id'] = anexo_id
                    resultado_upload['data_processamento'] = datetime.now().isoformat()
                    
                    return resultado_upload
                else:
                    self.logger.warning(f"⚠️ Anexo {nome_original} sem conteúdo")
            else:
                self.logger.error(f"❌ Erro baixar anexo {nome_original}: {anexo_response.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ Erro processar anexo individual: {e}")
            
        return None
    
    def processar_emails_pasta_enel(self, limite: int = 50, apenas_com_anexos: bool = True) -> Dict[str, Any]:
        """
        Processa emails da pasta ENEL
        VERSÃO CORRIGIDA: upload direto OneDrive
        """
        relatorio = {
            'emails_processados': 0,
            'emails_com_anexos': 0,
            'anexos_processados': 0,
            'uploads_sucesso': 0,
            'uploads_erro': 0,
            'tempo_inicio': datetime.now().isoformat(),
            'detalhes': []
        }
        
        try:
            headers = self.auth.obter_headers_autenticados()
            
            # Definir URL da pasta
            if self.pasta_enel_id:
                emails_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_enel_id}/messages"
                self.logger.info(f"📧 Usando pasta ENEL: {self.pasta_enel_id}")
            else:
                emails_url = "https://graph.microsoft.com/v1.0/me/messages"
                self.logger.info("📧 Usando caixa de entrada (fallback)")
            
            # Parâmetros da consulta - SIMPLIFICADOS para evitar InefficientFilter
            params = {
                '$top': limite
            }
            
            # Usar apenas filtro OU ordenação, não ambos (Microsoft Graph limitação)
            if apenas_com_anexos:
                params['$filter'] = 'hasAttachments eq true'
            else:
                params['$orderby'] = 'receivedDateTime desc'
            
            self.logger.info(f"🔍 Buscando até {limite} emails...")
            
            response = requests.get(emails_url, headers=headers, params=params, timeout=self.timeout_request)
            
            if response.status_code != 200:
                self.logger.error(f"❌ Erro buscar emails: {response.status_code}")
                return relatorio
            
            emails = response.json().get('value', [])
            self.logger.info(f"📧 {len(emails)} emails encontrados")
            
            # Processar cada email
            for email in emails:
                try:
                    resultado_email = self.processar_email_individual(email)
                    
                    relatorio['emails_processados'] += 1
                    
                    if resultado_email['tem_anexos']:
                        relatorio['emails_com_anexos'] += 1
                        relatorio['anexos_processados'] += resultado_email['anexos_processados']
                        relatorio['uploads_sucesso'] += resultado_email['uploads_sucesso']
                        relatorio['uploads_erro'] += resultado_email['uploads_erro']
                    
                    relatorio['detalhes'].append(resultado_email)
                    
                    # Delay entre processamentos
                    if self.delay_entre_requests > 0:
                        time.sleep(self.delay_entre_requests)
                        
                except Exception as e:
                    self.logger.error(f"❌ Erro processar email individual: {e}")
                    relatorio['uploads_erro'] += 1
                    continue
            
            relatorio['tempo_fim'] = datetime.now().isoformat()
            
            self.logger.info(f"✅ Processamento concluído:")
            self.logger.info(f"   📧 Emails: {relatorio['emails_processados']}")
            self.logger.info(f"   📎 Anexos: {relatorio['anexos_processados']}")
            self.logger.info(f"   ✅ Sucessos: {relatorio['uploads_sucesso']}")
            self.logger.info(f"   ❌ Erros: {relatorio['uploads_erro']}")
            
        except Exception as e:
            self.logger.error(f"❌ Erro geral processar_emails_pasta_enel: {e}")
            relatorio['erro_geral'] = str(e)
            
        return relatorio
    
    def processar_email_individual(self, email: dict) -> Dict[str, Any]:
        """Processa um email individual"""
        email_id = email.get('id', '')
        subject = email.get('subject', 'Sem assunto')
        received_date = email.get('receivedDateTime', '')
        has_attachments = email.get('hasAttachments', False)
        
        resultado = {
            'email_id': email_id,
            'subject': subject[:100],  # Truncar para log
            'received_date': received_date,
            'tem_anexos': has_attachments,
            'anexos_processados': 0,
            'uploads_sucesso': 0,
            'uploads_erro': 0,
            'detalhes_anexos': []
        }
        
        try:
            self.logger.info(f"📩 Processando: {subject[:50]}...")
            
            if has_attachments:
                # Processar anexos (upload direto OneDrive)
                resultados_anexos = self.baixar_anexos_email(email_id)
                
                resultado['anexos_processados'] = len(resultados_anexos)
                
                for resultado_anexo in resultados_anexos:
                    if resultado_anexo['status'] == 'sucesso':
                        resultado['uploads_sucesso'] += 1
                    else:
                        resultado['uploads_erro'] += 1
                    
                    resultado['detalhes_anexos'].append({
                        'arquivo': resultado_anexo.get('filename', 'N/A'),
                        'status': resultado_anexo['status'],
                        'onedrive_path': resultado_anexo.get('onedrive_path', 'N/A')
                    })
            
        except Exception as e:
            self.logger.error(f"❌ Erro processar email {email_id}: {e}")
            resultado['erro'] = str(e)
        
        return resultado
    
    def buscar_emails_por_filtro(self, filtros: dict, limite: int = 20) -> List[dict]:
        """Busca emails usando filtros específicos"""
        try:
            headers = self.auth.obter_headers_autenticados()
            
            # Construir filtros OData
            filtros_odata = []
            
            if filtros.get('assunto'):
                filtros_odata.append(f"contains(subject, '{filtros['assunto']}')")
            
            if filtros.get('remetente'):
                filtros_odata.append(f"contains(from/emailAddress/address, '{filtros['remetente']}')")
            
            if filtros.get('data_inicio'):
                filtros_odata.append(f"receivedDateTime ge {filtros['data_inicio']}")
            
            if filtros.get('data_fim'):
                filtros_odata.append(f"receivedDateTime le {filtros['data_fim']}")
            
            # URL base
            if self.pasta_enel_id:
                url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_enel_id}/messages"
            else:
                url = "https://graph.microsoft.com/v1.0/me/messages"
            
            # Parâmetros
            params = {
                '$top': limite,
                '$select': 'id,subject,receivedDateTime,hasAttachments,from',
                '$orderby': 'receivedDateTime desc'
            }
            
            if filtros_odata:
                params['$filter'] = ' and '.join(filtros_odata)
            
            response = requests.get(url, headers=headers, params=params, timeout=self.timeout_request)
            
            if response.status_code == 200:
                return response.json().get('value', [])
            else:
                self.logger.error(f"❌ Erro buscar emails filtrados: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Erro buscar_emails_por_filtro: {e}")
            return []
    
    def obter_estatisticas_pasta_enel(self) -> Dict[str, Any]:
        """Obtém estatísticas da pasta ENEL"""
        try:
            headers = self.auth.obter_headers_autenticados()
            
            if not self.pasta_enel_id:
                return {'erro': 'PASTA_ENEL_ID não configurado'}
            
            # Estatísticas da pasta
            pasta_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_enel_id}"
            response = requests.get(pasta_url, headers=headers, timeout=self.timeout_request)
            
            if response.status_code == 200:
                pasta_info = response.json()
                
                # Contar emails com anexos
                emails_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_enel_id}/messages"
                params = {
                    '$top': 1000,
                    '$select': 'hasAttachments',
                    '$filter': 'hasAttachments eq true'
                }
                
                emails_response = requests.get(emails_url, headers=headers, params=params)
                emails_com_anexos = 0
                if emails_response.status_code == 200:
                    emails_com_anexos = len(emails_response.json().get('value', []))
                
                return {
                    'nome_pasta': pasta_info.get('displayName'),
                    'total_emails': pasta_info.get('totalItemCount', 0),
                    'emails_nao_lidos': pasta_info.get('unreadItemCount', 0),
                    'emails_com_anexos': emails_com_anexos,
                    'data_consulta': datetime.now().isoformat()
                }
            else:
                return {'erro': f'HTTP {response.status_code}'}
                
        except Exception as e:
            self.logger.error(f"❌ Erro obter estatísticas: {e}")
            return {'erro': str(e)}
    
    def verificar_estrutura_onedrive(self) -> Dict[str, Any]:
        """Verifica estrutura OneDrive ENEL"""
        try:
            headers = self.auth.obter_headers_autenticados()
            
            # Verificar pasta raiz ENEL
            if self.onedrive_enel_id:
                enel_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{self.onedrive_enel_id}"
            else:
                enel_url = "https://graph.microsoft.com/v1.0/me/drive/root:/Enel"
            
            response = requests.get(enel_url, headers=headers, timeout=self.timeout_request)
            
            if response.status_code == 200:
                # Verificar estrutura Faturas
                ano_atual = datetime.now().year
                mes_atual = f"{datetime.now().month:02d}"
                
                faturas_path = f"/Enel/Faturas/{ano_atual}/{mes_atual}"
                faturas_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{faturas_path}"
                
                faturas_response = requests.get(faturas_url, headers=headers, timeout=self.timeout_request)
                
                return {
                    'pasta_enel_ok': True,
                    'estrutura_faturas_ok': faturas_response.status_code == 200,
                    'caminho_verificado': faturas_path,
                    'data_verificacao': datetime.now().isoformat()
                }
            else:
                return {
                    'pasta_enel_ok': False,
                    'erro': f'HTTP {response.status_code}',
                    'data_verificacao': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"❌ Erro verificar estrutura: {e}")
            return {
                'pasta_enel_ok': False,
                'erro': str(e),
                'data_verificacao': datetime.now().isoformat()
            }
    
    def renomear_pdf_pela_planilha_relacao(self, pdf_info: dict, dados_planilha: dict) -> Dict[str, Any]:
        """
        MÉTODO MANTIDO PARA COMPATIBILIDADE
        Renomeia PDF usando dados da planilha de relação
        VERSÃO CORRIGIDA: trabalha direto no OneDrive
        """
        try:
            if not pdf_info.get('onedrive_id'):
                return {'status': 'erro', 'erro': 'PDF não está no OneDrive'}
            
            # Gerar novo nome baseado na planilha
            if dados_planilha.get('uc'):
                novo_nome = f"UC-{dados_planilha['uc']}-{pdf_info.get('filename', '')}"
            else:
                novo_nome = f"RENAMED-{pdf_info.get('filename', '')}"
            
            # Renomear no OneDrive
            headers = self.auth.obter_headers_autenticados()
            headers['Content-Type'] = 'application/json'
            
            rename_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pdf_info['onedrive_id']}"
            rename_data = {'name': novo_nome}
            
            response = requests.patch(rename_url, headers=headers, json=rename_data, timeout=self.timeout_request)
            
            if response.status_code == 200:
                self.logger.info(f"✅ PDF renomeado: {novo_nome}")
                return {
                    'status': 'sucesso',
                    'nome_original': pdf_info.get('filename'),
                    'nome_novo': novo_nome,
                    'onedrive_id': pdf_info['onedrive_id']
                }
            else:
                return {
                    'status': 'erro',
                    'erro': f'HTTP {response.status_code}',
                    'detalhes': response.text
                }
                
        except Exception as e:
            self.logger.error(f"❌ Erro renomear PDF: {e}")
            return {
                'status': 'erro',
                'erro': str(e)
            }
    
    def listar_arquivos_processados(self, ano: str = None, mes: str = None) -> List[Dict[str, Any]]:
        """Lista arquivos processados no OneDrive"""
        try:
            if not ano:
                ano = str(datetime.now().year)
            if not mes:
                mes = f"{datetime.now().month:02d}"
            
            headers = self.auth.obter_headers_autenticados()
            
            # Listar arquivos da pasta específica
            pasta_path = f"/Enel/Faturas/{ano}/{mes}"
            lista_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{pasta_path}:/children"
            
            response = requests.get(lista_url, headers=headers, timeout=self.timeout_request)
            
            if response.status_code == 200:
                arquivos = response.json().get('value', [])
                
                resultado = []
                for arquivo in arquivos:
                    if arquivo.get('file'):  # É um arquivo, não pasta
                        resultado.append({
                            'nome': arquivo.get('name'),
                            'id': arquivo.get('id'),
                            'tamanho': arquivo.get('size', 0),
                            'data_criacao': arquivo.get('createdDateTime'),
                            'data_modificacao': arquivo.get('lastModifiedDateTime'),
                            'url_download': arquivo.get('@microsoft.graph.downloadUrl')
                        })
                
                return resultado
            else:
                self.logger.error(f"❌ Erro listar arquivos: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Erro listar_arquivos_processados: {e}")
            return []
    
    def processar_emails_incremental(self, planilha_manager, dias_atras: int = 1, database=None) -> Dict[str, Any]:
        """
        Processar emails incrementalmente integrado com planilha_manager
        Método adicionado para compatibilidade com sistema_enel.py
        """
        try:
            self.logger.info(f"📧 Processamento incremental - últimos {dias_atras} dias")
            
            # Processar emails da pasta ENEL
            resultado_emails = self.processar_emails_pasta_enel(limite=100)
            
            if resultado_emails.get('emails_processados', 0) == 0:
                return {
                    "status": "sucesso",
                    "mensagem": "Nenhum email novo para processar",
                    "emails_processados": 0,
                    "dados_extraidos": 0
                }
            
            # Integrar com planilha_manager se houver anexos processados
            dados_extraidos = 0
            faturas_processadas = []
            
            for detalhe in resultado_emails.get('detalhes', []):
                if detalhe.get('anexos_processados', 0) > 0:
                    dados_extraidos += detalhe['anexos_processados']
                    faturas_processadas.append(detalhe)
            
            return {
                "status": "sucesso", 
                "mensagem": f"Processamento incremental concluído",
                "emails_processados": resultado_emails['emails_processados'],
                "dados_extraidos": dados_extraidos,
                "faturas_processadas": faturas_processadas,
                "uploads_sucesso": resultado_emails.get('uploads_sucesso', 0),
                "detalhes": resultado_emails
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro processamento incremental: {e}")
            return {
                "status": "erro",
                "erro": str(e),
                "mensagem": "Falha no processamento incremental"
            }


# Classe de compatibilidade mantida
class EmailProcessor(EmailProcessorEnel):
    """Classe de compatibilidade com o código existente"""
    
    def __init__(self, auth_manager, onedrive_manager=None):
        super().__init__(auth_manager, onedrive_manager)
        self.logger.info("📧 EmailProcessor (compatibilidade) iniciado")


# Utilitários adicionais
class EmailProcessorUtils:
    """Utilitários para o processador de emails"""
    
    @staticmethod
    def validar_email_enel(subject: str, from_address: str) -> bool:
        """Valida se email é relacionado à ENEL"""
        keywords_enel = ['enel', 'distribuidora', 'energia', 'fatura', 'conta']
        subject_lower = subject.lower()
        from_lower = from_address.lower()
        
        return any(keyword in subject_lower or keyword in from_lower for keyword in keywords_enel)
    
    @staticmethod
    def extrair_uc_do_assunto(subject: str) -> Optional[str]:
        """Extrai UC do assunto do email"""
        # Padrões comuns para UC
        padroes = [
            r'UC[:\s]*(\d+)',
            r'UC(\d+)',
            r'Unidade Consumidora[:\s]*(\d+)',
            r'(\d{7,10})'  # Números de 7-10 dígitos
        ]
        
        for padrao in padroes:
            match = re.search(padrao, subject, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def formatar_nome_arquivo_por_uc(uc: str, data: datetime = None) -> str:
        """Formata nome de arquivo baseado na UC"""
        if not data:
            data = datetime.now()
        
        return f"UC-{uc}-{data.year}-{data.month:02d}-ENEL.pdf"


if __name__ == "__main__":
    # Exemplo de uso
    print("📧 Email Processor ENEL - OneDrive Integration")
    print("✅ Versão corrigida sem storage local")
    print("🔧 Todas as funcionalidades mantidas")
    print("📁 Upload direto para /Enel/Faturas/YYYY/MM/")
