#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚨 ALERT PROCESSOR ENEL - Processador de alertas automáticos
📧 FUNÇÃO: Processar alertas automáticos ENEL + anexar fatura PDF
👨‍💼 AUTOR: Baseado no alert_processor.py BRK funcionando
🔧 ADAPTADO: Para instalações ENEL em vez de CDCs BRK
📅 DATA: Sistema ENEL baseado na infraestrutura BRK
✅ REUTILIZAÇÃO: Mesma base alertas_bot.db e mesmo token Microsoft
"""

import os
import requests
import re
from datetime import datetime
from .enel_database import obter_responsaveis_por_casa_enel, buscar_responsaveis_por_instalacao
from .telegram_sender import enviar_telegram, enviar_telegram_com_anexo
from .message_formatter import formatar_mensagem_alerta_enel

# Import da função centralizada de cálculo ENEL
try:
    from processor.calculo_enel import calcular_media_e_diferenca_enel
    CALCULO_CENTRALIZADO = True
    print("✅ Sistema de alertas usando função centralizada de cálculo")
except ImportError:
    CALCULO_CENTRALIZADO = False
    print("⚠️ Função centralizada não disponível - alertas usarão valores da planilha")

# FUNÇÕES REMOVIDAS - AGORA CENTRALIZADAS
# As funções calcular_media_consumo_enel() e obter_historico_consumo_instalacao()
# foram movidas para processor/calculo_enel.py para centralização
# 
# ESTRATÉGIA ATUAL:
# - Planilha usa função centralizada para calcular valores
# - Alertas usam valores já calculados da planilha (mais seguro)
# - Garante consistência total entre planilha e alertas

def obter_historico_instalacao_database(database_manager, numero_instalacao):
    """
    Obter histórico de uma instalação usando o database SQLite
    
    Args:
        database_manager: Instância DatabaseEnel
        numero_instalacao: Número da instalação ENEL
        
    Returns:
        list: Histórico de consumo ordenado por data (mais recente primeiro)
    """
    try:
        if not database_manager:
            print("⚠️ Database manager não disponível")
            return []
        
        historico = database_manager.buscar_por_instalacao(numero_instalacao)
        
        if not historico:
            print(f"📊 Nenhum histórico encontrado para instalação {numero_instalacao}")
            return []
        
        # Converter para formato esperado pelas funções de cálculo
        historico_formatado = []
        for item in historico:
            try:
                historico_formatado.append({
                    "mes_ano": item.get("competencia", ""),
                    "consumo": item.get("consumo_kwh", 0),
                    "tipo": "HISTORICO",
                    "data_processamento": item.get("data_processamento", "")
                })
            except Exception as e:
                print(f"⚠️ Erro formatando item do histórico: {e}")
                continue
        
        # Ordenar por competência (mais recente primeiro)
        historico_formatado.sort(key=lambda x: x.get("mes_ano", ""), reverse=True)
        
        print(f"📊 Histórico obtido: {len(historico_formatado)} registros para instalação {numero_instalacao}")
        return historico_formatado
        
    except Exception as e:
        print(f"❌ Erro obtendo histórico do database: {e}")
        return []

def processar_alerta_fatura_enel(dados_fatura, relacionamentos_dados, onedrive_manager=None, database_manager=None):
    """
    Processar alerta de fatura ENEL com anexo PDF
    
    Fluxo:
    1. Extrair casa da instalação via planilha relacionamento
    2. Obter código CCB da casa
    3. Buscar responsáveis na base CCB (mesma do BRK)  
    4. Enviar alerta via Telegram com PDF anexado
    
    Args:
        dados_fatura (dict): Dados da fatura processada
        relacionamentos_dados (list): Planilha de relacionamento ENEL
        onedrive_manager: Manager OneDrive para baixar PDFs
        database_manager: Instância DatabaseEnel (opcional)
        
    Returns:
        dict: Resultado do processamento
    """
    try:
        print(f"\n🚨 INICIANDO PROCESSAMENTO ALERTA ENEL COM ANEXO")
        
        # 1. Extrair informações básicas
        numero_instalacao = dados_fatura.get('numero_instalacao', '')
        casa_oracao = dados_fatura.get('casa_oracao', '')
        arquivo_pdf = dados_fatura.get('arquivo_pdf', '')
        
        if not numero_instalacao:
            print(f"❌ Número de instalação não fornecido")
            return {"sucesso": False, "erro": "Instalação não informada"}
            
        print(f"📋 Processando alerta:")
        print(f"   ⚡ Instalação: {numero_instalacao}")
        print(f"   🏪 Casa: {casa_oracao}")
        print(f"   📄 PDF: {arquivo_pdf}")
        
        # 2. Buscar responsáveis pela instalação
        if casa_oracao:
            # Se já temos a casa, usar diretamente
            responsaveis = obter_responsaveis_por_casa_enel(casa_oracao)
        else:
            # Buscar casa pela instalação na planilha relacionamento  
            responsaveis = buscar_responsaveis_por_instalacao(numero_instalacao, relacionamentos_dados)
        
        if not responsaveis:
            print(f"⚠️ Nenhum responsável encontrado para instalação: {numero_instalacao}")
            return {
                "sucesso": False, 
                "erro": f"Responsáveis não encontrados",
                "instalacao": numero_instalacao,
                "casa": casa_oracao
            }
        
        print(f"👥 Responsáveis encontrados: {len(responsaveis)}")
        for resp in responsaveis:
            print(f"   👤 {resp['nome']} ({resp['funcao']}) - ID: {resp['user_id']}")
        
        # 3. Baixar PDF da fatura (se disponível e onedrive_manager fornecido)
        pdf_bytes = None
        nome_arquivo_pdf = arquivo_pdf or f"fatura_{numero_instalacao}.pdf"
        
        if onedrive_manager and arquivo_pdf:
            try:
                print(f"📥 Tentando baixar PDF: {arquivo_pdf}")
                
                # Buscar PDF na estrutura OneDrive ENEL
                pdf_bytes = onedrive_manager.baixar_pdf_fatura(arquivo_pdf)
                
                if pdf_bytes:
                    print(f"✅ PDF baixado: {len(pdf_bytes)} bytes")
                else:
                    print(f"⚠️ PDF não encontrado: {arquivo_pdf}")
                    
            except Exception as e:
                print(f"⚠️ Erro baixando PDF: {e}")
        
        # 4. Determinar tipo de alerta usando função central unificada
        from processor.classificador_consumo import determinar_tipo_alerta_consumo
        
        consumo_atual = dados_fatura.get('consumo_kwh_num', 0)
        media_6_meses = dados_fatura.get('media_6_meses', 0)
        
        # Se há dados de consumo suficientes, determinar tipo baseado no consumo
        if consumo_atual > 0 and media_6_meses > 0:
            classificacao = determinar_tipo_alerta_consumo(consumo_atual, media_6_meses)
            tipo_alerta_determinado = classificacao['tipo_alerta']
            
            # Adicionar dados da classificação aos dados da fatura para mensagem
            dados_fatura.update({
                'diferenca_percentual': classificacao['diferenca_percentual'],
                'diferenca_absoluta': classificacao['diferenca_absoluta'],
                'porcentagem_consumo': classificacao['porcentagem_consumo']
            })
            
            print(f"🎯 Tipo alerta determinado: {tipo_alerta_determinado} ({classificacao['classificacao']})")
        else:
            # Fallback para fatura pendente quando não há dados de consumo
            tipo_alerta_determinado = "fatura_pendente"
            print(f"📋 Usando tipo padrão: {tipo_alerta_determinado} (sem dados de consumo)")
        
        # 5. Formatar mensagem com tipo correto
        mensagem = formatar_mensagem_alerta_enel(
            dados_fatura, 
            responsaveis[0],  # Usar primeiro responsável para formatação
            tipo_alerta=tipo_alerta_determinado
        )
        
        print(f"📝 Mensagem formatada ({len(mensagem)} caracteres)")
        
        # 6. Enviar alertas para todos os responsáveis
        resultados_envio = []
        alertas_enviados = 0
        alertas_falharam = 0
        
        for responsavel in responsaveis:
            user_id = responsavel['user_id']
            nome = responsavel['nome']
            
            try:
                print(f"📤 Enviando alerta para: {nome} (ID: {user_id})")
                
                # Enviar com PDF se disponível
                if pdf_bytes:
                    sucesso = enviar_telegram_com_anexo(
                        user_id, 
                        mensagem, 
                        pdf_bytes, 
                        nome_arquivo_pdf
                    )
                else:
                    # Enviar apenas mensagem
                    sucesso = enviar_telegram(user_id, mensagem)
                
                if sucesso:
                    alertas_enviados += 1
                    print(f"✅ Alerta enviado com sucesso para: {nome}")
                    resultados_envio.append({
                        "responsavel": nome,
                        "user_id": user_id,
                        "status": "sucesso"
                    })
                else:
                    alertas_falharam += 1
                    print(f"❌ Falha enviando alerta para: {nome}")
                    resultados_envio.append({
                        "responsavel": nome, 
                        "user_id": user_id,
                        "status": "falha"
                    })
                    
            except Exception as e:
                alertas_falharam += 1
                print(f"❌ Erro enviando para {nome}: {e}")
                resultados_envio.append({
                    "responsavel": nome,
                    "user_id": user_id, 
                    "status": "erro",
                    "erro": str(e)
                })
        
        # 6. Resultado final
        resultado = {
            "sucesso": alertas_enviados > 0,
            "instalacao": numero_instalacao,
            "casa": casa_oracao,
            "responsaveis_encontrados": len(responsaveis),
            "alertas_enviados": alertas_enviados,
            "alertas_falharam": alertas_falharam,
            "pdf_anexado": bool(pdf_bytes),
            "detalhes": resultados_envio,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"📊 RESULTADO ALERTA ENEL:")
        print(f"   ✅ Sucessos: {alertas_enviados}")
        print(f"   ❌ Falhas: {alertas_falharam}")
        print(f"   📎 PDF anexado: {'Sim' if pdf_bytes else 'Não'}")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro processando alerta ENEL: {e}")
        return {
            "sucesso": False,
            "erro": str(e),
            "instalacao": dados_fatura.get('numero_instalacao', 'N/A'),
            "timestamp": datetime.now().isoformat()
        }

def processar_alertas_consumo_alto_enel(planilha_dados, relacionamentos_dados, limite_percentual=150, database_manager=None):
    """
    Processar alertas para faturas com consumo muito alto
    
    Args:
        planilha_dados (list): Dados da planilha de controle atual
        relacionamentos_dados (list): Dados da planilha relacionamento
        limite_percentual (int): Limite percentual para disparar alerta
        database_manager: Instância DatabaseEnel (opcional)
        
    Returns:
        dict: Resultado dos alertas de consumo
    """
    try:
        print(f"\n⚡ PROCESSANDO ALERTAS DE CONSUMO ALTO ENEL")
        print(f"📊 Limite configurado: {limite_percentual}%")
        
        alertas_processados = 0
        alertas_enviados = 0
        
        # Analisar cada fatura na planilha
        for registro in planilha_dados:
            try:
                status = registro.get('Status', '')
                
                # Só processar faturas recebidas
                if status != 'Recebida':
                    continue
                
                # ESTRATÉGIA: Usar valores já calculados da planilha (mais seguro e validado)
                # A função centralizada garante que planilha e alertas sempre batam
                consumo_atual = float(registro.get('Consumo_kWh', 0) or 0)
                media_6_meses = float(registro.get('Media_6_Meses', 0) or 0)
                diferenca_percentual = float(registro.get('Diferenca_Percentual', 0) or 0)
                
                # Verificar se há dados válidos para processar
                if media_6_meses == 0:
                    continue
                    
                if abs(diferenca_percentual) >= limite_percentual:
                    print(f"🚨 Consumo alto detectado:")
                    print(f"   🏪 Casa: {registro.get('Casa de Oração', 'N/A')}")
                    print(f"   ⚡ Instalação: {registro.get('Numero_Instalacao', 'N/A')}")
                    print(f"   📊 Variação: {diferenca_percentual:+.1f}%")
                    
                    # Preparar dados para alerta (valores já validados da planilha ENEL)
                    dados_alerta = {
                        'casa_oracao': registro.get('Casa de Oração', ''),
                        'numero_instalacao': registro.get('Numero_Instalacao', ''),
                        'valor_total': float(registro.get('Valor_Total', 0) or 0),
                        'data_vencimento': registro.get('Data_Vencimento', ''),
                        'consumo_kwh': consumo_atual,  # ✅ DA PLANILHA (já validado)
                        'media_6_meses': media_6_meses,  # ✅ DA PLANILHA (já validado)  
                        'diferenca_percentual': diferenca_percentual,  # ✅ DA PLANILHA (já validado)
                        'alerta_consumo': registro.get('Alerta_Consumo', f'Consumo {diferenca_percentual:+.1f}% acima da média')
                    }
                    
                    # Processar alerta
                    resultado = processar_alerta_fatura_enel(
                        dados_alerta,
                        relacionamentos_dados
                    )
                    
                    alertas_processados += 1
                    if resultado.get('sucesso'):
                        alertas_enviados += resultado.get('alertas_enviados', 0)
                        
            except Exception as e:
                print(f"⚠️ Erro processando registro de consumo: {e}")
                continue
        
        resultado = {
            "sucesso": alertas_processados > 0,
            "alertas_processados": alertas_processados,
            "alertas_enviados": alertas_enviados,
            "limite_usado": limite_percentual,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"📊 RESUMO ALERTAS CONSUMO ALTO:")
        print(f"   🔍 Analisados: {len(planilha_dados)}")
        print(f"   🚨 Processados: {alertas_processados}")
        print(f"   📤 Enviados: {alertas_enviados}")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro processando alertas de consumo: {e}")
        return {
            "sucesso": False,
            "erro": str(e),
            "timestamp": datetime.now().isoformat()
        }

def processar_resumo_mensal_enel(status_controle, admin_ids=None):
    """
    Enviar resumo mensal para administradores
    
    Args:
        status_controle (dict): Status do controle mensal
        admin_ids (list): IDs dos administradores
        
    Returns:
        dict: Resultado do envio
    """
    try:
        print(f"\n📊 PROCESSANDO RESUMO MENSAL ENEL")
        
        # IDs dos administradores
        if not admin_ids:
            # NOVA LÓGICA: Buscar administradores da base CCB Alerta
            admin_ids_str = self._obter_administradores_da_base()
            admin_ids = [aid.strip() for aid in admin_ids_str.split(",") if aid.strip()]
        
        if not admin_ids:
            print(f"⚠️ Nenhum administrador encontrado na base CCB Alerta")
            return {"sucesso": False, "erro": "Administradores não configurados"}
        
        # Preparar dados do resumo
        dados_resumo = {
            'total_processadas': status_controle.get('faturas_recebidas', 0),
            'total_faltantes': status_controle.get('faturas_faltando', 0),
            'valor_total_mensal': status_controle.get('valor_total_processado', 0),
            'mes_referencia': datetime.now().strftime("%m/%Y"),
            'percentual_completo': status_controle.get('percentual_recebidas', 0)
        }
        
        # Formatar mensagem
        mensagem = formatar_mensagem_alerta_enel(
            dados_resumo,
            {"nome": "Administrador", "funcao": "Sistema"},
            tipo_alerta="resumo_processamento"
        )
        
        # Enviar para todos os administradores
        resultados = []
        sucessos = 0
        
        for admin_id in admin_ids:
            try:
                print(f"📤 Enviando resumo para admin: {admin_id}")
                sucesso = enviar_telegram(admin_id, mensagem)
                
                if sucesso:
                    sucessos += 1
                    print(f"✅ Resumo enviado para admin: {admin_id}")
                else:
                    print(f"❌ Falha enviando para admin: {admin_id}")
                    
                resultados.append({
                    "admin_id": admin_id,
                    "sucesso": sucesso
                })
                
            except Exception as e:
                print(f"❌ Erro enviando para admin {admin_id}: {e}")
                resultados.append({
                    "admin_id": admin_id,
                    "sucesso": False,
                    "erro": str(e)
                })
        
        resultado = {
            "sucesso": sucessos > 0,
            "admins_contatados": sucessos,
            "total_admins": len(admin_ids),
            "detalhes": resultados,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"📊 RESUMO MENSAL ENVIADO:")
        print(f"   ✅ Sucessos: {sucessos}/{len(admin_ids)}")
        
        return resultado
    
    def _obter_administradores_da_base(self) -> str:
        """
        Obter IDs dos administradores da base CCB Alerta
        
        Returns:
            str: IDs dos administradores separados por vírgula
        """
        try:
            import sqlite3
            import os
            
            # Caminho da base CCB Alerta
            db_path = os.path.join(os.getcwd(), 'alertas_bot.db')
            
            if not os.path.exists(db_path):
                print(f"⚠️ Base CCB Alerta não encontrada: {db_path}")
                return ""
            
            # Conectar e buscar administradores
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT user_id FROM administradores WHERE user_id IS NOT NULL")
            admins = cursor.fetchall()
            
            conn.close()
            
            if admins:
                admin_ids = [str(admin[0]) for admin in admins]
                admin_ids_str = ",".join(admin_ids)
                print(f"👥 Administradores encontrados na base: {len(admins)} ({admin_ids_str})")
                return admin_ids_str
            else:
                print(f"⚠️ Nenhum administrador encontrado na base CCB Alerta")
                return ""
                
        except Exception as e:
            print(f"❌ Erro buscando administradores da base: {e}")
            # Fallback para variável de ambiente se houver erro
            return os.getenv("ADMIN_IDS", "")

def testar_alertas_enel():
    """
    Função de teste para verificar sistema de alertas ENEL
    """
    try:
        print(f"\n🧪 TESTE SISTEMA ALERTAS ENEL")
        print(f"=" * 40)
        
        # Testar configurações
        from .enel_database import testar_conexao_enel_ccb
        from .telegram_sender import verificar_configuracao_telegram
        
        # Teste 1: Conexão com base CCB
        print(f"1️⃣ Testando conexão ENEL → CCB...")
        ccb_ok = testar_conexao_enel_ccb()
        
        # Teste 2: Configuração Telegram
        print(f"\n2️⃣ Testando configuração Telegram...")
        telegram_config = verificar_configuracao_telegram()
        telegram_ok = telegram_config.get('bot_token_valido', False) and len(telegram_config.get('admin_ids_validos', [])) > 0
        
        # Teste 3: Enviar mensagem de teste
        if telegram_ok:
            print(f"\n3️⃣ Enviando mensagem de teste...")
            admin_ids = telegram_config.get('admin_ids_validos', [])
            if admin_ids:
                from .message_formatter import formatar_mensagem_teste_enel
                mensagem_teste = formatar_mensagem_teste_enel()
                
                sucesso = enviar_telegram(admin_ids[0], mensagem_teste)
                print(f"📤 Teste mensagem: {'✅ OK' if sucesso else '❌ Falhou'}")
            else:
                print(f"❌ Nenhum admin ID válido para teste")
                sucesso = False
        else:
            print(f"⚠️ Configuração Telegram inválida - pulando teste de mensagem")
            sucesso = False
        
        # Resultado final
        tudo_ok = ccb_ok and telegram_ok and sucesso
        
        print(f"\n📊 RESULTADO TESTE ALERTAS ENEL:")
        print(f"   🗃️ Base CCB: {'✅ OK' if ccb_ok else '❌ Falhou'}")
        print(f"   📱 Telegram: {'✅ OK' if telegram_ok else '❌ Falhou'}")
        print(f"   📤 Envio: {'✅ OK' if sucesso else '❌ Falhou'}")
        print(f"   🎯 Geral: {'✅ SUCESSO' if tudo_ok else '❌ PROBLEMAS DETECTADOS'}")
        
        return {
            "sucesso_geral": tudo_ok,
            "base_ccb": ccb_ok,
            "telegram": telegram_ok,
            "envio_teste": sucesso,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Erro teste alertas ENEL: {e}")
        return {
            "sucesso_geral": False,
            "erro": str(e),
            "timestamp": datetime.now().isoformat()
        }