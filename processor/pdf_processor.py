"""
PDF Processor ENEL - Versão COMPLETA CORRIGIDA
OneDrive integration - sem storage local
"""

import os
import logging
import requests
import io
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional
import PyPDF2
import pdfplumber

class PDFProcessorEnel:
    """
    Processador de PDFs ENEL com integração OneDrive
    Versão corrigida - SEM storage local
    """
    
    def __init__(self, auth_manager, onedrive_manager=None):
        self.auth = auth_manager
        self.onedrive_manager = onedrive_manager
        self.logger = logging.getLogger(__name__)
        
        # REMOVIDO: Storage local - OneDrive only
        # self.storage_dir = None
        # self.pdfs_dir = None  
        # self.planilhas_dir = None
        
        # Configurações ENEL
        self.onedrive_enel_id = os.getenv("ONEDRIVE_ENEL_ID")
        
        self.logger.info("📄 PDFProcessorEnel iniciado - OneDrive ONLY")
    
    def upload_pdf_to_onedrive(self, pdf_content: bytes, filename: str, subfolder: str = None) -> Dict[str, Any]:
        """
        Upload PDF para OneDrive /Enel/
        
        Args:
            pdf_content: Conteúdo PDF em bytes
            filename: Nome do arquivo
            subfolder: Subpasta (ex: "Processados", "Faturas/2025/08")
            
        Returns:
            Resultado do upload
        """
        try:
            # Definir caminho OneDrive
            if subfolder:
                onedrive_path = f"/Enel/{subfolder}/{filename}"
            else:
                onedrive_path = f"/Enel/{filename}"
            
            headers = self.auth.obter_headers_autenticados()
            headers['Content-Type'] = 'application/pdf'
            
            # Upload
            upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{onedrive_path}:/content"
            response = requests.put(upload_url, headers=headers, data=pdf_content, timeout=60)
            
            if response.status_code in [200, 201]:
                file_info = response.json()
                self.logger.info(f"✅ PDF uploaded: {filename}")
                
                return {
                    'status': 'sucesso',
                    'onedrive_path': onedrive_path,
                    'onedrive_id': file_info.get('id'),
                    'size': len(pdf_content),
                    'filename': filename
                }
            else:
                return {
                    'status': 'erro',
                    'erro': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            self.logger.error(f"❌ Erro upload PDF: {e}")
            return {
                'status': 'erro',
                'erro': str(e)
            }
    
    def processar_pdf_content(self, pdf_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Processa PDF direto da memória (sem arquivo local)
        
        Args:
            pdf_content: Conteúdo do PDF em bytes
            filename: Nome do arquivo
            
        Returns:
            Dados extraídos do PDF
        """
        try:
            # Criar objeto de arquivo em memória
            pdf_file = io.BytesIO(pdf_content)
            
            # Extrair texto com pdfplumber
            dados_extraidos = {
                'filename': filename,
                'texto_completo': '',
                'paginas': 0,
                'dados_enel': {},
                'status': 'sucesso'
            }
            
            with pdfplumber.open(pdf_file) as pdf:
                dados_extraidos['paginas'] = len(pdf.pages)
                
                texto_completo = []
                for i, page in enumerate(pdf.pages):
                    texto_pagina = page.extract_text() or ''
                    texto_completo.append(texto_pagina)
                    
                    # Extrair dados específicos ENEL da primeira página
                    if i == 0:
                        dados_extraidos['dados_enel'] = self.extrair_dados_enel_pdf(texto_pagina)
                
                dados_extraidos['texto_completo'] = '\n'.join(texto_completo)
            
            self.logger.info(f"✅ PDF processado: {filename} ({dados_extraidos['paginas']} páginas)")
            return dados_extraidos
            
        except Exception as e:
            self.logger.error(f"❌ Erro processar PDF {filename}: {e}")
            return {
                'filename': filename,
                'status': 'erro',
                'erro': str(e)
            }
    
    def extrair_dados_enel_pdf(self, texto: str) -> Dict[str, Any]:
        """
        Extrai dados específicos ENEL do texto do PDF
        """
        import re
        
        dados = {}
        
        try:
            # UC (Unidade Consumidora)
            uc_match = re.search(r'UC[:\s]*(\d+)', texto, re.IGNORECASE)
            if uc_match:
                dados['uc'] = uc_match.group(1)
            
            # Valor da fatura
            valor_patterns = [
                r'Total a pagar[:\s]*R\$[:\s]*([0-9.,]+)',
                r'Valor total[:\s]*R\$[:\s]*([0-9.,]+)',
                r'R\$[:\s]*([0-9.,]+)'
            ]
            
            for pattern in valor_patterns:
                valor_match = re.search(pattern, texto, re.IGNORECASE)
                if valor_match:
                    dados['valor'] = valor_match.group(1)
                    break
            
            # Data de vencimento
            venc_patterns = [
                r'Vencimento[:\s]*(\d{2}/\d{2}/\d{4})',
                r'Data limite[:\s]*(\d{2}/\d{2}/\d{4})',
                r'(\d{2}/\d{2}/\d{4})'
            ]
            
            for pattern in venc_patterns:
                venc_match = re.search(pattern, texto)
                if venc_match:
                    dados['vencimento'] = venc_match.group(1)
                    break
            
            # Consumo kWh
            consumo_match = re.search(r'(\d+)\s*kWh', texto, re.IGNORECASE)
            if consumo_match:
                dados['consumo_kwh'] = consumo_match.group(1)
            
            # Período
            periodo_match = re.search(r'(\d{2}/\d{4})', texto)
            if periodo_match:
                dados['periodo'] = periodo_match.group(1)
                
        except Exception as e:
            self.logger.error(f"❌ Erro extrair dados ENEL: {e}")
            
        return dados
    
    def validar_pdf_enel(self, pdf_content: bytes) -> Dict[str, Any]:
        """
        Valida se PDF é uma fatura ENEL válida
        """
        try:
            dados = self.processar_pdf_content(pdf_content, "temp_validation.pdf")
            
            if dados['status'] == 'erro':
                return {'valido': False, 'motivo': 'Erro processar PDF'}
            
            texto = dados['texto_completo'].lower()
            
            # Verificar palavras-chave ENEL
            keywords_enel = ['enel', 'distribuidora', 'energia elétrica', 'kwh', 'unidade consumidora']
            keywords_found = sum(1 for keyword in keywords_enel if keyword in texto)
            
            if keywords_found >= 2:
                return {
                    'valido': True,
                    'confianca': min(100, keywords_found * 25),
                    'dados_extraidos': dados['dados_enel']
                }
            else:
                return {
                    'valido': False,
                    'motivo': 'Não parece ser fatura ENEL',
                    'keywords_found': keywords_found
                }
                
        except Exception as e:
            return {
                'valido': False,
                'motivo': f'Erro validação: {str(e)}'
            }
    
    def processar_lote_pdfs(self, pdfs_info: List[Dict]) -> Dict[str, Any]:
        """
        Processa lote de PDFs
        
        Args:
            pdfs_info: Lista com info dos PDFs [{'content': bytes, 'filename': str}]
            
        Returns:
            Relatório do processamento
        """
        relatorio = {
            'total_pdfs': len(pdfs_info),
            'processados_sucesso': 0,
            'processados_erro': 0,
            'uploads_sucesso': 0,
            'uploads_erro': 0,
            'detalhes': []
        }
        
        try:
            for pdf_info in pdfs_info:
                try:
                    filename = pdf_info['filename']
                    pdf_content = pdf_info['content']
                    
                    self.logger.info(f"📄 Processando PDF: {filename}")
                    
                    # Processar PDF
                    dados_pdf = self.processar_pdf_content(pdf_content, filename)
                    
                    if dados_pdf['status'] == 'sucesso':
                        relatorio['processados_sucesso'] += 1
                        
                        # Upload para OneDrive
                        agora = datetime.now()
                        subfolder = f"Faturas/{agora.year}/{agora.month:02d}"
                        
                        resultado_upload = self.upload_pdf_to_onedrive(
                            pdf_content, filename, subfolder
                        )
                        
                        if resultado_upload['status'] == 'sucesso':
                            relatorio['uploads_sucesso'] += 1
                        else:
                            relatorio['uploads_erro'] += 1
                        
                        # Adicionar ao relatório
                        relatorio['detalhes'].append({
                            'filename': filename,
                            'processamento': 'sucesso',
                            'upload': resultado_upload['status'],
                            'dados_extraidos': dados_pdf.get('dados_enel', {}),
                            'onedrive_path': resultado_upload.get('onedrive_path')
                        })
                        
                    else:
                        relatorio['processados_erro'] += 1
                        relatorio['detalhes'].append({
                            'filename': filename,
                            'processamento': 'erro',
                            'erro': dados_pdf.get('erro', 'N/A')
                        })
                        
                except Exception as e:
                    self.logger.error(f"❌ Erro processar PDF individual {pdf_info.get('filename', 'N/A')}: {e}")
                    relatorio['processados_erro'] += 1
                    continue
            
            self.logger.info(f"✅ Lote processado: {relatorio['processados_sucesso']}/{relatorio['total_pdfs']} sucessos")
            
        except Exception as e:
            self.logger.error(f"❌ Erro processar lote: {e}")
            relatorio['erro_geral'] = str(e)
            
        return relatorio


# Classe de compatibilidade
class PDFProcessor(PDFProcessorEnel):
    """Classe de compatibilidade"""
    pass


if __name__ == "__main__":
    print("📄 PDF Processor ENEL - OneDrive Integration")
    print("✅ Processamento direto em memória")
    print("🔧 Upload automático para OneDrive")
    print("📁 Estrutura: /Enel/Faturas/YYYY/MM/")
