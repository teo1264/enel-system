#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: processor/email_processor.py
💾 FUNÇÃO: Processador de emails ENEL (RENDER COMPATÍVEL)
🔧 DESCRIÇÃO: Download e processamento de emails da pasta ENEL
👨‍💼 AUTOR: Adaptado do BRK para ENEL
🔒 BASEADO EM: funcionalidade do sistema desktop ENEL

⚡ IMPORTANTE: Sistema funciona SEM pandas no Render
🌐 Compatible com deploy Render usando versões sem pandas
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import base64
from pathlib import Path

class EmailProcessor:
    """
    Processador de emails ENEL
    
    Responsabilidades:
    - Buscar emails da pasta específica ENEL
    - Baixar anexos PDF dos emails
    - Filtrar emails por período
    - Integrar com Microsoft Graph API
    """
    
    def __init__(self, auth_manager):
        """
        Inicializar processador com autenticação
        
        Args:
            auth_manager: Instância do MicrosoftAuth
        """
        self.auth = auth_manager
        self.pasta_enel_id = os.getenv("PASTA_ENEL_ID")
        
        # Cache de emails processados (controle duplicatas - padrão BRK)
        self.emails_processados_cache = set()
        
        # Diretório para salvar PDFs
        self.download_dir = "/opt/render/project/storage/pdfs_enel"
        os.makedirs(self.download_dir, exist_ok=True)
        
        print(f"📧 EmailProcessor ENEL inicializado")
        print(f"   Pasta ID: {'configurada' if self.pasta_enel_id else 'pendente'}")
        print(f"   Download dir: {self.download_dir}")
    
    def diagnosticar_pasta_enel(self) -> Dict:
        """
        Diagnosticar acesso à pasta ENEL
        
        Returns:
            Dict: Informações sobre a pasta e conectividade
        """
        try:
            if not self.auth.access_token:
                return {
                    "status": "erro",
                    "mensagem": "Token não disponível"
                }
            
            if not self.pasta_enel_id:
                return {
                    "status": "erro",
                    "mensagem": "PASTA_ENEL_ID não configurada"
                }
            
            headers = self.auth.obter_headers_autenticados()
            
            # Testar acesso à pasta
            url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_enel_id}"
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 401:
                # Tentar renovar token
                if self.auth.tentar_renovar_se_necessario(401):
                    headers = self.auth.obter_headers_autenticados()
                    response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                pasta_info = response.json()
                
                # Buscar alguns emails recentes para teste
                emails_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_enel_id}/messages?$top=5&$select=subject,receivedDateTime,from"
                emails_response = requests.get(emails_url, headers=headers, timeout=15)
                
                emails_recentes = []
                if emails_response.status_code == 200:
                    emails_data = emails_response.json()
                    for email in emails_data.get('value', []):
                        emails_recentes.append({
                            "assunto": email.get('subject', 'N/A'),
                            "data": email.get('receivedDateTime', 'N/A'),
                            "remetente": email.get('from', {}).get('emailAddress', {}).get('address', 'N/A')
                        })
                
                return {
                    "status": "sucesso",
                    "pasta": {
                        "nome": pasta_info.get('displayName', 'N/A'),
                        "id": self.pasta_enel_id,
                        "total_mensagens": pasta_info.get('totalItemCount', 0),
                        "nao_lidas": pasta_info.get('unreadItemCount', 0)
                    },
                    "emails_recentes": emails_recentes,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "erro",
                    "mensagem": f"Erro acessando pasta: HTTP {response.status_code}",
                    "pasta_id": self.pasta_enel_id
                }
                
        except Exception as e:
            return {
                "status": "erro",
                "mensagem": f"Erro no diagnóstico: {str(e)}"
            }
    
    def buscar_emails_enel(self, dias_atras: int = 7) -> List[Dict]:
        """
        Buscar emails da pasta ENEL por período
        
        Args:
            dias_atras (int): Quantos dias atrás buscar
            
        Returns:
            List[Dict]: Lista de emails encontrados
        """
        try:
            if not self.auth.access_token or not self.pasta_enel_id:
                print("❌ Token ou pasta ENEL não configurados")
                return []
            
            headers = self.auth.obter_headers_autenticados()
            
            # Calcular data de início
            data_inicio = datetime.now() - timedelta(days=dias_atras)
            data_filtro = data_inicio.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            # Buscar emails com filtro de data
            url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{self.pasta_enel_id}/messages"
            params = {
                '$filter': f"receivedDateTime ge {data_filtro}",
                '$orderby': 'receivedDateTime desc',
                '$select': 'id,subject,receivedDateTime,from,hasAttachments,body',
                '$top': 50  # Limitar para evitar timeout
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 401:
                # Tentar renovar token
                if self.auth.tentar_renovar_se_necessario(401):
                    headers = self.auth.obter_headers_autenticados()
                    response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                emails = data.get('value', [])
                
                # Filtrar apenas emails com anexos (faturas ENEL têm PDFs)
                emails_com_anexos = [email for email in emails if email.get('hasAttachments', False)]
                
                print(f"📧 Encontrados {len(emails)} emails, {len(emails_com_anexos)} com anexos")
                return emails_com_anexos
            else:
                print(f"❌ Erro buscando emails: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Erro na busca de emails: {e}")
            return []
    
    def baixar_anexos_email(self, email: Dict) -> List[str]:
        """
        Baixar anexos PDF de um email específico
        
        Args:
            email (Dict): Dados do email
            
        Returns:
            List[str]: Lista de caminhos dos PDFs baixados
        """
        try:
            email_id = email.get('id')
            if not email_id:
                return []
            
            headers = self.auth.obter_headers_autenticados()
            
            # Buscar anexos do email
            url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}/attachments"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Erro buscando anexos: HTTP {response.status_code}")
                return []
            
            attachments_data = response.json()
            pdfs_baixados = []
            
            for attachment in attachments_data.get('value', []):
                # Verificar se é PDF
                nome_arquivo = attachment.get('name', '').lower()
                if not nome_arquivo.endswith('.pdf'):
                    continue
                
                # Baixar o anexo
                attachment_id = attachment.get('id')
                if not attachment_id:
                    continue
                
                attachment_url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}/attachments/{attachment_id}"
                attachment_response = requests.get(attachment_url, headers=headers, timeout=30)
                
                if attachment_response.status_code == 200:
                    attachment_data = attachment_response.json()
                    
                    # Decodificar conteúdo base64
                    content_bytes = base64.b64decode(attachment_data.get('contentBytes', ''))
                    
                    # Salvar arquivo
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    nome_arquivo_seguro = f"enel_{timestamp}_{nome_arquivo.replace(' ', '_')}"
                    caminho_arquivo = os.path.join(self.download_dir, nome_arquivo_seguro)
                    
                    with open(caminho_arquivo, 'wb') as f:
                        f.write(content_bytes)
                    
                    pdfs_baixados.append(caminho_arquivo)
                    print(f"📎 PDF baixado: {nome_arquivo_seguro}")
            
            return pdfs_baixados
            
        except Exception as e:
            print(f"❌ Erro baixando anexos: {e}")
            return []
    
    def renomear_pdf_pela_planilha_relacao(self, pdf_path: str, dados_fatura: Dict, planilha_manager) -> Optional[str]:
        """
        Renomear PDF baseado na planilha de relacionamento ENEL
        
        Args:
            pdf_path: Caminho atual do PDF
            dados_fatura: Dados extraídos da fatura
            planilha_manager: Manager para acessar planilha relacionamento
            
        Returns:
            dict: {
                'caminho': str,           # Novo caminho do PDF
                'casa_completa': str,     # Nome completo da casa
                'codigo_alertas': str,    # Código para busca na alertas_bot.db
                'nome_arquivo': str       # Nome do arquivo renomeado
            } ou None se erro
        """
        try:
            numero_instalacao = dados_fatura.get('numero_instalacao')
            data_vencimento = dados_fatura.get('data_vencimento')  # DD/MM/YYYY
            
            if not numero_instalacao or not data_vencimento:
                print(f"⚠️ Dados insuficientes para renomeação: instalação={numero_instalacao}, vencimento={data_vencimento}")
                return None
            
            # Garantir que planilha relacionamento esteja carregada DINAMICAMENTE
            if not hasattr(planilha_manager, 'relacionamentos_dados') or not planilha_manager.relacionamentos_dados:
                print(f"🔄 Carregando planilha relacionamento do OneDrive...")
                if not planilha_manager.carregar_planilha_relacionamento():
                    print(f"❌ ERRO: Não foi possível carregar planilha relacionamento do OneDrive")
                    return None
            
            casa_encontrada = None
            for relacao in planilha_manager.relacionamentos_dados:
                if str(relacao.get('instalacao', '')).strip() == str(numero_instalacao).strip():
                    casa_encontrada = relacao.get('casa_oracao', '').strip()
                    break
            
            if not casa_encontrada:
                print(f"⚠️ Casa não encontrada para instalação {numero_instalacao}")
                return None
            
            # Casa completa (ex: "BR 21-0270 - CENTRO") 
            casa_completa = casa_encontrada.strip()
            
            # CONVERTER: Planilha relacionamento → Padrão base alertas_bot.db
            # Simples: nomes são predefinidos (não há variações de digitação)
            if casa_completa == 'ADM – MAUA – SP':
                codigo_casa_padrao = 'ADM-MAUÁ'
            elif casa_completa == 'PIA':
                codigo_casa_padrao = 'PIA'
            else:
                # Padrão BR: "BR 21-0270 - CENTRO" → "BR21-0270"
                codigo_casa_padrao = casa_completa.split(' - ')[0].replace(' ', '')
            
            # Salvar ambos: nome completo (planilha) + código padrão (alertas)
            dados_fatura_extras = {
                'casa_oracao_completa': casa_completa,      # Para renomeação de arquivo
                'codigo_casa_alertas': codigo_casa_padrao,  # Para busca na base comum
                'casa_oracao': codigo_casa_padrao           # Campo principal (padrão comum)
            }
            
            # Extrair competência dos dados da fatura
            competencia = dados_fatura.get('competencia', '')  # MM/YYYY
            valor_total = dados_fatura.get('valor_total_num', 0.0)
            
            # Formatar data de vencimento (DD/MM/YYYY → DD-MM e DD-MM-YYYY)
            try:
                if '/' in data_vencimento:
                    partes_data = data_vencimento.split('/')
                    dd_mm = f"{partes_data[0]:0>2}-{partes_data[1]:0>2}"
                    dd_mm_yyyy = f"{partes_data[0]:0>2}-{partes_data[1]:0>2}-{partes_data[2]}"
                else:
                    dd_mm = "00-00"
                    dd_mm_yyyy = "00-00-0000"
            except:
                dd_mm = "00-00"
                dd_mm_yyyy = "00-00-0000"
            
            # Formatar competência (MM/YYYY → MM-YYYY)
            try:
                if '/' in competencia:
                    partes_comp = competencia.split('/')
                    mm_yyyy = f"{partes_comp[0]:0>2}-{partes_comp[1]}"
                else:
                    mm_yyyy = "00-0000"
            except:
                mm_yyyy = "00-0000"
            
            # Formatar valor (123.45 → 123.45)
            valor_formatado = f"{valor_total:.2f}".replace('.', ',')
            
            # Formato CORRETO: DD-MM-ENEL MM-YYYY - CASA_COMPLETA - vc. DD-MM-YYYY - R$ VALOR.pdf
            nome_arquivo = f"{dd_mm}-ENEL {mm_yyyy} - {casa_completa} - vc. {dd_mm_yyyy} - R$ {valor_formatado}.pdf"
            novo_caminho = os.path.join(os.path.dirname(pdf_path), nome_arquivo)
            
            # Renomear arquivo
            if os.path.exists(pdf_path):
                os.rename(pdf_path, novo_caminho)
                print(f"🏷️ PDF renomeado: {os.path.basename(pdf_path)} → {nome_arquivo}")
                print(f"🔗 Código para alertas: {codigo_casa_padrao}")
                
                return {
                    'caminho': novo_caminho,
                    'casa_completa': casa_completa,
                    'codigo_alertas': codigo_casa_padrao,
                    'nome_arquivo': nome_arquivo,
                    'dados_extras': dados_fatura_extras
                }
            else:
                print(f"❌ Arquivo não existe para renomeação: {pdf_path}")
                return None
                
        except Exception as e:
            print(f"❌ Erro renomeando PDF: {e}")
            return None
    
    def processar_emails_incremental(self, planilha_manager, dias_atras: int = 7, database_manager=None) -> Dict:
        """
        Processamento incremental de emails ENEL com planilha de controle
        
        Args:
            planilha_manager: Instância do PlanilhaManagerEnel
            dias_atras (int): Período para processar
            database_manager: Instância DatabaseEnel (opcional)
            
        Returns:
            Dict: Resultado do processamento incremental
        """
        try:
            print(f"🔄 Iniciando processamento incremental ENEL - {dias_atras} dias")
            
            # 1. Buscar emails novos
            emails = self.buscar_emails_enel(dias_atras)
            
            if not emails:
                return {
                    "status": "sucesso",
                    "mensagem": f"Nenhum email ENEL encontrado nos últimos {dias_atras} dia(s)",
                    "emails_processados": 0,
                    "faturas_processadas": 0
                }
            
            # 2. Importar processador PDF
            from .pdf_processor import PDFProcessor
            pdf_processor = PDFProcessor()
            
            # 3. Processar cada email incrementalmente
            emails_processados = 0
            faturas_processadas = 0
            faturas_com_erro = 0
            emails_duplicados = 0
            faturas_atualizadas = []
            
            for i, email in enumerate(emails, 1):
                try:
                    email_id = email.get('id')
                    email_subject = email.get('subject', 'Sem assunto')[:50]
                    
                    # CONTROLE DE DUPLICATAS (padrão BRK)
                    if email_id and email_id in self.emails_processados_cache:
                        print(f"🔄 EMAIL JÁ PROCESSADO: {i}/{len(emails)} - {email_subject}")
                        emails_duplicados += 1
                        continue  # Pular email já processado
                    
                    print(f"📧 Processando email {i}/{len(emails)}: {email_subject}")
                    
                    # Adicionar ao cache ANTES do processamento
                    if email_id:
                        self.emails_processados_cache.add(email_id)
                    
                    # Baixar PDFs do email
                    pdfs_baixados = self.baixar_anexos_email(email)
                    
                    if pdfs_baixados:
                        # Processar cada PDF
                        for pdf_path in pdfs_baixados:
                            # PASSO 1: Remover proteção IMEDIATAMENTE (OBRIGATÓRIO)
                            if not pdf_processor.remover_protecao_pdf(pdf_path):
                                print(f"❌ ERRO: Não foi possível descriptografar {os.path.basename(pdf_path)}")
                                faturas_com_erro += 1
                                continue
                            
                            # PASSO 2: Extrair dados do PDF desprotegido
                            dados_fatura = pdf_processor.extrair_dados_fatura(pdf_path)
                            
                            if dados_fatura:
                                # PASSO 3: Renomear PDF baseado na planilha de relacionamento
                                resultado_renomeacao = self.renomear_pdf_pela_planilha_relacao(
                                    pdf_path, dados_fatura, planilha_manager
                                )
                                if resultado_renomeacao:
                                    pdf_path = resultado_renomeacao['caminho']
                                    # IMPORTANTE: Usar código padrão da base alertas_bot.db (REFERÊNCIA COMUM)
                                    dados_extras = resultado_renomeacao['dados_extras']
                                    dados_fatura.update(dados_extras)
                                    dados_fatura['nome_arquivo_renomeado'] = os.path.basename(pdf_path)
                                    print(f"✅ Casa padronizada: {dados_fatura['casa_oracao']} (código comum para alertas)")
                            
                            if dados_fatura:
                                # Verificar se valor foi extraído corretamente
                                valor_extraido = dados_fatura.get('valor_total_num')
                                if valor_extraido is None:
                                    print(f"❌ ALERTA CRÍTICO: Fatura {dados_fatura.get('arquivo')} sem valor extraído!")
                                    print(f"   🔍 Requerer verificação manual da extração")
                                    faturas_com_erro += 1
                                
                                # Salvar no database (se disponível)
                                database_salvo = False
                                if database_manager:
                                    try:
                                        with open(pdf_path, 'rb') as f:
                                            pdf_content = f.read()
                                        database_salvo = database_manager.inserir_fatura(dados_fatura, email_id, pdf_content)
                                        if database_salvo:
                                            print(f"💾 Fatura salva no database SQLite")
                                    except Exception as e:
                                        print(f"⚠️ Erro salvando no database: {e}")
                                
                                # Processar incrementalmente na planilha
                                if planilha_manager.processar_fatura_incremental(dados_fatura):
                                    faturas_processadas += 1
                                    
                                    # Adicionar info para relatório
                                    faturas_atualizadas.append({
                                        'instalacao': dados_fatura.get('numero_instalacao', 'N/A'),
                                        'valor': dados_fatura.get('valor_total_num') or 'ERRO_EXTRAÇÃO',
                                        'arquivo': dados_fatura.get('arquivo', 'N/A'),
                                        'database_salvo': database_salvo
                                    })
                    
                    emails_processados += 1
                    
                except Exception as e:
                    print(f"❌ Erro processando email {i}: {e}")
                    continue
            
            # 4. Atualizar estatísticas de duplicatas no PlanilhaManager
            planilha_manager.estatisticas_duplicatas["emails_duplicados"] = emails_duplicados
            planilha_manager.estatisticas_duplicatas["timestamp_processamento"] = datetime.now().isoformat()
            
            # 5. Salvar planilha atualizada COM aba de resumo
            planilha_salva = planilha_manager.salvar_controle_mensal()
            
            # 6. Obter status atual
            status_controle = planilha_manager.obter_status_controle()
            
            resultado = {
                "status": "sucesso",
                "mensagem": "Processamento incremental ENEL finalizado",
                "processamento": {
                    "emails_processados": emails_processados,
                    "emails_duplicados_ignorados": emails_duplicados,
                    "faturas_processadas": faturas_processadas,
                    "faturas_com_erro_valor": faturas_com_erro,
                    "periodo_dias": dias_atras
                },
                "controle_mensal": status_controle,
                "faturas_atualizadas": faturas_atualizadas,
                "planilha_salva": planilha_salva,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"✅ Processamento incremental concluído:")
            print(f"   📧 Emails processados: {emails_processados}")
            if emails_duplicados > 0:
                print(f"   🔄 Emails duplicados ignorados: {emails_duplicados}")
            print(f"   ⚡ Faturas atualizadas: {faturas_processadas}")
            print(f"   📊 Status: {status_controle.get('faturas_recebidas', 0)}/{status_controle.get('total_instalacoes', 0)}")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro no processamento incremental: {e}")
            return {
                "status": "erro",
                "mensagem": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def processar_emails_completo(self, dias_atras: int = 7) -> Dict:
        """
        Processamento completo de emails ENEL (modo compatibilidade)
        
        Args:
            dias_atras (int): Período para processar
            
        Returns:
            Dict: Resultado do processamento
        """
        try:
            print(f"🔄 Iniciando processamento completo ENEL - {dias_atras} dias")
            
            # 1. Buscar emails
            emails = self.buscar_emails_enel(dias_atras)
            
            if not emails:
                return {
                    "status": "sucesso",
                    "mensagem": f"Nenhum email ENEL encontrado nos últimos {dias_atras} dia(s)",
                    "emails_processados": 0,
                    "pdfs_baixados": 0
                }
            
            # 2. Processar cada email
            emails_processados = 0
            total_pdfs = 0
            
            for i, email in enumerate(emails, 1):
                try:
                    print(f"📧 Processando email {i}/{len(emails)}: {email.get('subject', 'N/A')[:50]}")
                    
                    # Baixar PDFs
                    pdfs = self.baixar_anexos_email(email)
                    total_pdfs += len(pdfs)
                    
                    emails_processados += 1
                    
                except Exception as e:
                    print(f"❌ Erro processando email {i}: {e}")
                    continue
            
            resultado = {
                "status": "sucesso",
                "mensagem": "Processamento de emails finalizado",
                "emails_processados": emails_processados,
                "pdfs_baixados": total_pdfs,
                "periodo_dias": dias_atras,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"✅ Processamento concluído:")
            print(f"   📧 Emails: {emails_processados}")
            print(f"   📎 PDFs: {total_pdfs}")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro no processamento completo: {e}")
            return {
                "status": "erro",
                "mensagem": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def limpar_pdfs_antigos(self, dias_manter: int = 30):
        """
        Limpar PDFs antigos do storage
        
        Args:
            dias_manter (int): Quantos dias manter os PDFs
        """
        try:
            if not os.path.exists(self.download_dir):
                return
            
            limite_data = datetime.now() - timedelta(days=dias_manter)
            arquivos_removidos = 0
            
            for arquivo in os.listdir(self.download_dir):
                caminho_arquivo = os.path.join(self.download_dir, arquivo)
                
                if os.path.isfile(caminho_arquivo):
                    # Verificar idade do arquivo
                    timestamp_arquivo = datetime.fromtimestamp(os.path.getctime(caminho_arquivo))
                    
                    if timestamp_arquivo < limite_data:
                        os.remove(caminho_arquivo)
                        arquivos_removidos += 1
            
            if arquivos_removidos > 0:
                print(f"🧹 Removidos {arquivos_removidos} PDFs antigos")
                
        except Exception as e:
            print(f"⚠️ Erro na limpeza de PDFs: {e}")
    
    def obter_cache_duplicatas_info(self) -> Dict:
        """
        Obter informações sobre cache de duplicatas
        
        Returns:
            Dict: Estatísticas do cache
        """
        return {
            "emails_em_cache": len(self.emails_processados_cache),
            "controle_duplicatas_ativo": True,
            "padrao_brk": "Implementado conforme BRK"
        }
    
    def obter_estatisticas(self) -> Dict:
        """
        Obter estatísticas do processamento
        
        Returns:
            Dict: Estatísticas atuais
        """
        try:
            stats = {
                "sistema": "ENEL Email Processor",
                "pasta_configurada": bool(self.pasta_enel_id),
                "pasta_id": self.pasta_enel_id,
                "download_dir": self.download_dir,
                "timestamp": datetime.now().isoformat()
            }
            
            # Contar PDFs no storage
            if os.path.exists(self.download_dir):
                pdfs = [f for f in os.listdir(self.download_dir) if f.lower().endswith('.pdf')]
                stats["pdfs_storage"] = len(pdfs)
                
                # Tamanho total
                tamanho_total = sum(
                    os.path.getsize(os.path.join(self.download_dir, f)) 
                    for f in pdfs
                )
                stats["tamanho_storage_mb"] = round(tamanho_total / (1024 * 1024), 2)
            else:
                stats["pdfs_storage"] = 0
                stats["tamanho_storage_mb"] = 0
            
            return stats
            
        except Exception as e:
            return {
                "erro": str(e),
                "timestamp": datetime.now().isoformat()
            }