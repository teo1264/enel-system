#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: processor/sistema_enel.py
💾 FUNÇÃO: Sistema principal ENEL - Orquestração completa
🔧 DESCRIÇÃO: Centraliza todas as funcionalidades ENEL
👨‍💼 AUTOR: Baseado no padrão BRK - app.py limpo
🔒 ESTRUTURA: Uma classe que gerencia tudo
"""

import os
from datetime import datetime
from typing import Dict, Optional
import logging

# Imports dos módulos ENEL
from .email_processor import EmailProcessor
from .pdf_processor import PDFProcessor
from .onedrive_manager import OneDriveManagerEnel
from .planilha_manager import PlanilhaManagerEnel
from .database_enel import DatabaseEnel

# Imports do sistema de alertas
from .alertas.alert_processor import (
    processar_alerta_fatura_enel, 
    processar_alertas_consumo_alto_enel,
    processar_resumo_mensal_enel,
    testar_alertas_enel
)

logger = logging.getLogger(__name__)

class SistemaEnel:
    """
    Sistema principal ENEL - Orquestração completa
    
    Centraliza todas as funcionalidades:
    - Estrutura OneDrive
    - Planilhas de controle
    - Processamento incremental
    - Status e relatórios
    """
    
    def __init__(self, auth_manager):
        """
        Inicializar sistema ENEL
        
        Args:
            auth_manager: Instância MicrosoftAuth
        """
        self.auth = auth_manager
        
        # Componentes do sistema (inicializados sob demanda)
        self._email_processor = None
        self._pdf_processor = None
        self._onedrive_manager = None
        self._planilha_manager = None
        self._database = None
        
        print("⚡ Sistema ENEL inicializado")
    
    @property
    def email_processor(self):
        """Lazy loading do email processor"""
        if self._email_processor is None:
            self._email_processor = EmailProcessor(self.auth)
        return self._email_processor
    
    @property
    def pdf_processor(self):
        """Lazy loading do PDF processor"""
        if self._pdf_processor is None:
            self._pdf_processor = PDFProcessor()
        return self._pdf_processor
    
    @property
    def onedrive_manager(self):
        """Lazy loading do OneDrive manager"""
        if self._onedrive_manager is None:
            self._onedrive_manager = OneDriveManagerEnel(self.auth)
        return self._onedrive_manager
    
    @property
    def planilha_manager(self):
        """Lazy loading do planilha manager"""
        if self._planilha_manager is None:
            self._planilha_manager = PlanilhaManagerEnel(self.auth, self.onedrive_manager, self.database)
        return self._planilha_manager
    
    @property
    def database(self):
        """Lazy loading do database manager"""
        if self._database is None:
            self._database = DatabaseEnel(self.onedrive_manager)
        return self._database
    
    def diagnosticar_pasta_enel(self) -> Dict:
        """
        Diagnóstico da pasta ENEL no Outlook
        
        Returns:
            Dict: Resultado do diagnóstico
        """
        try:
            if not self.auth.access_token:
                return {"erro": "Token não disponível"}
            
            return self.email_processor.diagnosticar_pasta_enel()
            
        except Exception as e:
            logger.error(f"Erro diagnóstico pasta: {e}")
            return {"erro": str(e)}
    
    def criar_estrutura_onedrive(self) -> Dict:
        """
        Criar estrutura completa OneDrive ENEL
        
        Returns:
            Dict: Resultado da criação
        """
        try:
            if not self.auth.access_token:
                return {"erro": "Token não disponível"}
            
            sucesso = self.onedrive_manager.garantir_estrutura_completa()
            
            if sucesso:
                ids_estrutura = self.onedrive_manager.obter_ids_estrutura()
                
                return {
                    "status": "sucesso",
                    "mensagem": "Estrutura OneDrive ENEL criada com sucesso!",
                    "estrutura": {
                        "pasta_enel": bool(ids_estrutura["pasta_enel"]),
                        "pasta_faturas": bool(ids_estrutura["pasta_faturas"]),
                        "pasta_planilhas": bool(ids_estrutura["pasta_planilhas"])
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "erro",
                    "mensagem": "Falha ao criar estrutura OneDrive ENEL"
                }
                
        except Exception as e:
            logger.error(f"Erro criando estrutura: {e}")
            return {"erro": str(e)}
    
    def testar_onedrive(self) -> Dict:
        """
        Testar conectividade OneDrive
        
        Returns:
            Dict: Status da conectividade
        """
        try:
            if not self.auth.access_token:
                return {"erro": "Token não disponível"}
            
            return self.onedrive_manager.testar_conectividade()
            
        except Exception as e:
            logger.error(f"Erro testando OneDrive: {e}")
            return {"erro": str(e)}
    
    def processar_emails_incremental(self, dias_atras: int = 1) -> Dict:
        """
        Processar emails ENEL incrementalmente
        
        Args:
            dias_atras (int): Período para processar
            
        Returns:
            Dict: Resultado do processamento
        """
        try:
            if not self.auth.access_token:
                return {"erro": "Token não disponível"}
            
            print(f"🔄 PROCESSAMENTO ENEL INCREMENTAL - últimos {dias_atras} dia(s)")
            
            # 1. Garantir estrutura OneDrive
            estrutura_ok = self.onedrive_manager.garantir_estrutura_completa()
            if not estrutura_ok:
                return {"erro": "Falha criando estrutura OneDrive"}
            
            # 2. Carregar planilha de relacionamento
            relacionamento_ok = self.planilha_manager.carregar_planilha_relacionamento_sem_pandas()
            if not relacionamento_ok:
                return {"erro": "Falha carregando planilha de relacionamento"}
            
            # 3. Carregar/criar controle mensal
            controle_ok = self.planilha_manager.carregar_planilha_controle_mensal()
            if not controle_ok:
                return {"erro": "Falha carregando controle mensal"}
            
            # 4. Processar emails incrementalmente
            resultado = self.email_processor.processar_emails_incremental(
                self.planilha_manager, 
                dias_atras,
                self.database
            )
            
            # 5. Processar alertas se houve processamento de faturas
            if resultado.get("status") == "sucesso" and resultado.get("dados_extraidos", 0) > 0:
                try:
                    print(f"\n🚨 Processando alertas automaticamente...")
                    
                    # Obter dados das faturas processadas (simulado - adapte conforme necessário)
                    faturas_processadas = resultado.get("faturas_processadas", [])
                    
                    if faturas_processadas:
                        alerta_resultado = self.processar_alertas_faturas(faturas_processadas)
                        resultado["alertas"] = alerta_resultado
                    
                    # Verificar alertas de consumo alto
                    consumo_resultado = self.processar_alertas_consumo_alto()
                    resultado["alertas_consumo"] = consumo_resultado
                    
                except Exception as e:
                    print(f"⚠️ Erro processando alertas: {e}")
                    resultado["alertas_erro"] = str(e)
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro processamento incremental: {e}")
            return {"erro": str(e)}
    
    def processar_emails_completo(self, dias_atras: int = 7) -> Dict:
        """
        Processar emails ENEL modo completo (compatibilidade)
        
        Args:
            dias_atras (int): Período para processar
            
        Returns:
            Dict: Resultado do processamento
        """
        try:
            if not self.auth.access_token:
                return {"erro": "Token não disponível"}
            
            print(f"🔄 PROCESSAMENTO ENEL COMPLETO - últimos {dias_atras} dia(s)")
            
            # Processar modo tradicional
            emails = self.email_processor.buscar_emails_enel(dias_atras)
            
            if not emails:
                return {
                    "status": "sucesso",
                    "mensagem": f"Nenhum email ENEL encontrado nos últimos {dias_atras} dia(s)",
                    "emails_processados": 0
                }
            
            emails_processados = 0
            pdfs_baixados = 0
            pdfs_desprotegidos = 0
            dados_extraidos = 0
            
            for i, email in enumerate(emails, 1):
                try:
                    print(f"📧 Processando email {i}/{len(emails)}")
                    
                    pdfs = self.email_processor.baixar_anexos_email(email)
                    if pdfs:
                        pdfs_baixados += len(pdfs)
                        
                        for pdf_path in pdfs:
                            if self.pdf_processor.remover_protecao_pdf(pdf_path):
                                pdfs_desprotegidos += 1
                            
                            dados_pdf = self.pdf_processor.extrair_dados_fatura(pdf_path)
                            if dados_pdf:
                                dados_extraidos += 1
                    
                    emails_processados += 1
                    
                except Exception as e:
                    print(f"❌ Erro processando email {i}: {e}")
                    continue
            
            # Gerar planilha final
            planilhas_geradas = 0
            if dados_extraidos > 0:
                try:
                    planilha_gerada = self.pdf_processor.gerar_planilha_consolidada()
                    if planilha_gerada:
                        planilhas_geradas = 1
                except Exception as e:
                    print(f"⚠️ Erro gerando planilha: {e}")
            
            return {
                "status": "sucesso",
                "mensagem": "Processamento ENEL completo finalizado",
                "emails_processados": emails_processados,
                "pdfs_baixados": pdfs_baixados,
                "pdfs_desprotegidos": pdfs_desprotegidos,
                "dados_extraidos": dados_extraidos,
                "planilhas_geradas": planilhas_geradas,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro processamento completo: {e}")
            return {"erro": str(e)}
    
    def obter_status_controle_mensal(self) -> Dict:
        """
        Obter status do controle mensal ENEL
        
        Returns:
            Dict: Status detalhado
        """
        try:
            if not self.auth.access_token:
                return {"erro": "Token não disponível"}
            
            # Carregar planilha de relacionamento
            relacionamento_ok = self.planilha_manager.carregar_planilha_relacionamento_sem_pandas()
            if not relacionamento_ok:
                return {"erro": "Planilha de relacionamento não disponível"}
            
            # Carregar controle mensal
            controle_ok = self.planilha_manager.carregar_planilha_controle_mensal()
            if not controle_ok:
                return {"erro": "Controle mensal não disponível"}
            
            # Obter status
            return self.planilha_manager.obter_status_controle()
            
        except Exception as e:
            logger.error(f"Erro obtendo status controle: {e}")
            return {"erro": str(e)}
    
    def processar_modo_hibrido(self, dados_request: Dict) -> Dict:
        """
        Processar emails ENEL - modo híbrido (incremental ou completo)
        
        Args:
            dados_request (Dict): Dados da requisição
            
        Returns:
            Dict: Resultado do processamento
        """
        try:
            dias_atras = dados_request.get('dias_atras', 1)
            modo = dados_request.get('modo', 'incremental')
            
            if modo == 'incremental':
                return self.processar_emails_incremental(dias_atras)
            else:
                return self.processar_emails_completo(dias_atras)
                
        except Exception as e:
            logger.error(f"Erro processamento híbrido: {e}")
            return {"erro": str(e)}
    
    def obter_estatisticas_sistema(self) -> Dict:
        """
        Obter estatísticas gerais do sistema
        
        Returns:
            Dict: Estatísticas completas
        """
        try:
            stats = {
                "sistema": "ENEL Render Web",
                "autenticado": bool(self.auth.access_token),
                "timestamp": datetime.now().isoformat()
            }
            
            # Stats dos componentes
            if self._email_processor:
                stats["email_processor"] = self.email_processor.obter_estatisticas()
            
            if self._pdf_processor:
                stats["pdf_processor"] = self.pdf_processor.obter_estatisticas()
            
            if self._onedrive_manager:
                stats["onedrive"] = self.onedrive_manager.testar_conectividade()
            
            if self._database:
                stats["database"] = self.database.obter_estatisticas()
            
            return stats
            
        except Exception as e:
            return {"erro": str(e), "timestamp": datetime.now().isoformat()}
    
    # ============================================================================
    # SISTEMA DE ALERTAS ENEL
    # ============================================================================
    
    def processar_alertas_faturas(self, dados_faturas, relacionamentos_dados=None) -> Dict:
        """
        Processar alertas para faturas ENEL
        
        Args:
            dados_faturas (list): Lista de dados das faturas processadas
            relacionamentos_dados (list): Dados planilha relacionamento (opcional)
            
        Returns:
            Dict: Resultado dos alertas processados
        """
        try:
            print(f"\n🚨 PROCESSANDO ALERTAS FATURAS ENEL")
            
            if not dados_faturas:
                return {
                    "sucesso": False,
                    "erro": "Nenhuma fatura para processar alertas",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Obter relacionamentos se não fornecidos
            if not relacionamentos_dados:
                try:
                    relacionamentos_dados = self.planilha_manager.obter_dados_relacionamento_enel()
                except Exception as e:
                    print(f"⚠️ Erro obtendo relacionamentos: {e}")
                    relacionamentos_dados = []
            
            # Processar alertas para cada fatura
            resultados = []
            sucessos_totais = 0
            
            for dados_fatura in dados_faturas:
                try:
                    resultado = processar_alerta_fatura_enel(
                        dados_fatura,
                        relacionamentos_dados,
                        self.onedrive_manager,
                        self.database
                    )
                    
                    resultados.append(resultado)
                    if resultado.get('sucesso'):
                        sucessos_totais += resultado.get('alertas_enviados', 0)
                        
                except Exception as e:
                    print(f"❌ Erro processando alerta fatura: {e}")
                    resultados.append({
                        "sucesso": False,
                        "erro": str(e),
                        "instalacao": dados_fatura.get('numero_instalacao', 'N/A')
                    })
            
            return {
                "sucesso": sucessos_totais > 0,
                "faturas_processadas": len(dados_faturas),
                "alertas_enviados_total": sucessos_totais,
                "detalhes": resultados,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro processando alertas faturas: {e}")
            return {
                "sucesso": False,
                "erro": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def processar_alertas_consumo_alto(self, limite_percentual=150) -> Dict:
        """
        Processar alertas de consumo alto baseado na planilha de controle
        
        Args:
            limite_percentual (int): Limite para disparar alerta (padrão: 150%)
            
        Returns:
            Dict: Resultado dos alertas de consumo
        """
        try:
            print(f"\n⚡ PROCESSANDO ALERTAS CONSUMO ALTO ENEL")
            
            # Obter dados da planilha de controle atual
            status_controle = self.obter_status_controle_mensal()
            if "erro" in status_controle:
                return {
                    "sucesso": False,
                    "erro": "Erro obtendo planilha de controle",
                    "detalhes": status_controle["erro"]
                }
            
            planilha_dados = status_controle.get('dados_detalhados', [])
            if not planilha_dados:
                return {
                    "sucesso": False,
                    "erro": "Nenhum dado na planilha de controle",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Obter relacionamentos
            try:
                relacionamentos_dados = self.planilha_manager.obter_dados_relacionamento_enel()
            except Exception as e:
                print(f"⚠️ Erro obtendo relacionamentos: {e}")
                relacionamentos_dados = []
            
            # Processar alertas de consumo alto
            resultado = processar_alertas_consumo_alto_enel(
                planilha_dados,
                relacionamentos_dados, 
                limite_percentual,
                self.database
            )
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro processando alertas consumo alto: {e}")
            return {
                "sucesso": False,
                "erro": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def enviar_resumo_mensal_admin(self, admin_ids=None) -> Dict:
        """
        Enviar resumo mensal para administradores
        
        Args:
            admin_ids (list): Lista de IDs dos administradores (opcional)
            
        Returns:
            Dict: Resultado do envio do resumo
        """
        try:
            print(f"\n📊 ENVIANDO RESUMO MENSAL ADMIN ENEL")
            
            # Obter status do controle mensal
            status_controle = self.obter_status_controle_mensal()
            if "erro" in status_controle:
                return {
                    "sucesso": False,
                    "erro": "Erro obtendo dados para resumo",
                    "detalhes": status_controle["erro"]
                }
            
            # Processar resumo mensal
            resultado = processar_resumo_mensal_enel(status_controle, admin_ids)
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro enviando resumo mensal: {e}")
            return {
                "sucesso": False,
                "erro": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def testar_sistema_alertas(self) -> Dict:
        """
        Testar todo o sistema de alertas ENEL
        
        Returns:
            Dict: Resultado dos testes
        """
        try:
            print(f"\n🧪 TESTANDO SISTEMA ALERTAS ENEL")
            
            resultado = testar_alertas_enel()
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro testando sistema alertas: {e}")
            return {
                "sucesso_geral": False,
                "erro": str(e),
                "timestamp": datetime.now().isoformat()
            }