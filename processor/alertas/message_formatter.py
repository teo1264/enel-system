#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📝 MESSAGE FORMATTER ENEL - Formatação mensagens Telegram
📧 FUNÇÃO: Formatar mensagens de alerta ENEL para Telegram
👨‍💼 AUTOR: Baseado no message_formatter.py BRK 
🔧 ADAPTADO: Para faturas ENEL em vez de faturas BRK
📅 DATA: Baseado no sistema BRK funcionando
🆕 VERSÃO: Com nova lógica de escalonamento e destaque fotovoltaico
"""

from datetime import datetime

def formatar_mensagem_alerta_enel(dados_fatura, responsavel_info, tipo_alerta="fatura_pendente"):
    """
    Formatar mensagem de alerta ENEL para Telegram
    
    Args:
        dados_fatura (dict): Dados da fatura ENEL
        responsavel_info (dict): Informações do responsável
        tipo_alerta (str): Tipo do alerta
        
    Returns:
        str: Mensagem formatada para Telegram
    """
    try:
        # Extrair dados principais
        casa_oracao = dados_fatura.get('casa_oracao', 'Casa não informada')
        numero_instalacao = dados_fatura.get('numero_instalacao', 'N/A')
        valor_total = dados_fatura.get('valor_total_num', 0)
        data_vencimento = dados_fatura.get('data_vencimento', '')
        consumo_kwh = dados_fatura.get('consumo_kwh_num', 0)
        
        # Informações do responsável
        nome_responsavel = responsavel_info.get('nome', 'Responsável')
        funcao_responsavel = responsavel_info.get('funcao', '')
        
        # Data/hora atual
        agora = datetime.now().strftime("%d/%m/%Y às %H:%M")
        
        if tipo_alerta == "fatura_pendente":
            # Verificar se tem sistema fotovoltaico
            sistema_fotovoltaico = dados_fatura.get('sistema_fotovoltaico', 'Não')
            
            mensagem_base = f"""A Paz de Deus! 

📍 Casa de Oração: {casa_oracao}  
⚡ Instalação ENEL: {numero_instalacao}  
📅 Vencimento: {data_vencimento}  
💰 Valor da Conta: R$ {valor_total:.2f}  

━━━━━━━━━━━━━━━━  
📊 Consumo Atual: {consumo_kwh} kWh  """
            
            # Adicionar informações fotovoltaicas se aplicável
            if sistema_fotovoltaico == 'Sim':
                energia_compensada = dados_fatura.get('energia_compensada_num', 0)
                total_compensacao = dados_fatura.get('total_compensacao', 0)
                percentual_economia = dados_fatura.get('percentual_economia_fv', 0)
                valor_sem_fv = dados_fatura.get('valor_integral_sem_fv', 0)
                
                mensagem_fotovoltaica = f"""☀️ Economia Fotovoltaica: R$ {total_compensacao:.2f} ({percentual_economia:.1f}%)  
💡 Sem fotovoltaico seria: R$ {valor_sem_fv:.2f}  
✅ Sistema solar funcionando  """
                mensagem_base += mensagem_fotovoltaica
            else:
                mensagem_base += "✅ Consumo dentro do padrão  "
            
            mensagem = mensagem_base + f"""━━━━━━━━━━━━━━━━  

⚠️ ATENÇÃO: Fatura ainda não recebida pelo sistema  

🤖 Sistema ENEL Automático  
🙏 Deus abençoe!"""

        elif tipo_alerta == "consumo_critico":
            media_6_meses = dados_fatura.get('media_6_meses', 0)
            diferenca_percentual = dados_fatura.get('diferenca_percentual', 0) 
            diferenca_absoluta = consumo_kwh - media_6_meses if media_6_meses > 0 else 0
            sistema_fotovoltaico = dados_fatura.get('sistema_fotovoltaico', 'Não')
            
            mensagem_base = f"""A Paz de Deus! 

🔴 CONSUMO CRÍTICO  

📍 Casa de Oração: {casa_oracao}  
⚡ Instalação ENEL: {numero_instalacao}  
📅 Vencimento: {data_vencimento}  
💰 Valor da Conta: R$ {valor_total:.2f}  

━━━━━━━━━━━━━━━━  
📊 Consumo Atual: {consumo_kwh} kWh  
📉 Média (6 meses): {media_6_meses} kWh  
📈 Aumento: +{diferenca_absoluta:.0f} kWh ({diferenca_percentual:.1f}%)  """
            
            # ALERTA ESPECIAL sobre fotovoltaico mascarando consumo
            if sistema_fotovoltaico == 'Sim':
                total_compensacao = dados_fatura.get('total_compensacao', 0)
                valor_sem_fv = dados_fatura.get('valor_integral_sem_fv', 0)
                mensagem_base += f"""⚠️ ATENÇÃO: Fotovoltaico mascarando consumo!  
💰 Sem fotovoltaico seria: R$ {valor_sem_fv:.2f}  
☀️ Economia atual: R$ {total_compensacao:.2f}  """
            
            mensagem = mensagem_base + f"""━━━━━━━━━━━━━━━━  

🚨 AÇÃO URGENTE:  
🔹 Verificar ar condicionado (principal causa)  
🔹 Confirmar se equipamentos foram desligados  
🔹 Investigar uso excessivo de energia  

🤖 Sistema ENEL Automático  
🙏 Deus abençoe!"""

        elif tipo_alerta == "consumo_alto":
            media_6_meses = dados_fatura.get('media_6_meses', 0)
            diferenca_percentual = dados_fatura.get('diferenca_percentual', 0)
            diferenca_absoluta = consumo_kwh - media_6_meses if media_6_meses > 0 else 0
            sistema_fotovoltaico = dados_fatura.get('sistema_fotovoltaico', 'Não')
            
            mensagem_base = f"""A Paz de Deus! 

🟠 CONSUMO ALTO  

📍 Casa de Oração: {casa_oracao}  
⚡ Instalação ENEL: {numero_instalacao}  
📅 Vencimento: {data_vencimento}  
💰 Valor da Conta: R$ {valor_total:.2f}  

━━━━━━━━━━━━━━━━  
📊 Consumo Atual: {consumo_kwh} kWh  
📉 Média (6 meses): {media_6_meses} kWh  
📈 Aumento: +{diferenca_absoluta:.0f} kWh ({diferenca_percentual:.1f}%)  """
            
            # ALERTA sobre fotovoltaico mascarando consumo
            if sistema_fotovoltaico == 'Sim':
                total_compensacao = dados_fatura.get('total_compensacao', 0)
                valor_sem_fv = dados_fatura.get('valor_integral_sem_fv', 0)
                mensagem_base += f"""⚠️ Fotovoltaico pode estar mascarando alto consumo  
💰 Sem fotovoltaico seria: R$ {valor_sem_fv:.2f}  
☀️ Economia: R$ {total_compensacao:.2f}  """
            else:
                mensagem_base += "⚠️ Consumo bem acima da média  "
            
            mensagem = mensagem_base + f"""━━━━━━━━━━━━━━━━  

🚨 INVESTIGAR:  
🔹 Ar condicionado pode ter ficado ligado  
🔹 Verificar equipamentos elétricos  
🔹 Monitorar próximas faturas  

🤖 Sistema ENEL Automático  
🙏 Deus abençoe!"""

        elif tipo_alerta == "consumo_acima_media":
            media_6_meses = dados_fatura.get('media_6_meses', 0)
            diferenca_percentual = dados_fatura.get('diferenca_percentual', 0)
            diferenca_absoluta = consumo_kwh - media_6_meses if media_6_meses > 0 else 0
            sistema_fotovoltaico = dados_fatura.get('sistema_fotovoltaico', 'Não')
            
            mensagem_base = f"""A Paz de Deus! 

🟡 CONSUMO ACIMA DA MÉDIA  

📍 Casa de Oração: {casa_oracao}  
⚡ Instalação ENEL: {numero_instalacao}  
📅 Vencimento: {data_vencimento}  
💰 Valor da Conta: R$ {valor_total:.2f}  

━━━━━━━━━━━━━━━━  
📊 Consumo Atual: {consumo_kwh} kWh  
📉 Média (6 meses): {media_6_meses} kWh  
📈 Aumento: +{diferenca_absoluta:.0f} kWh ({diferenca_percentual:.1f}%)  """
            
            # Informação sobre fotovoltaico se aplicável
            if sistema_fotovoltaico == 'Sim':
                total_compensacao = dados_fatura.get('total_compensacao', 0)
                mensagem_base += f"""☀️ Economia Fotovoltaica: R$ {total_compensacao:.2f}  """
            
            mensagem = mensagem_base + f"""━━━━━━━━━━━━━━━━  

ℹ️ INFORMATIVO:  
🔹 Aumento dentro do aceitável  
🔹 Monitorar próximas faturas  
🔹 Verificar se foi uso pontual  
{'🔹 Ar condicionado pode ter sido usado mais  ' if sistema_fotovoltaico == 'Não' else '🔹 Sistema fotovoltaico compensando parcialmente  '}

🤖 Sistema ENEL Automático  
🙏 Deus abençoe!"""

        elif tipo_alerta == "consumo_moderado":
            media_6_meses = dados_fatura.get('media_6_meses', 0)
            diferenca_percentual = dados_fatura.get('diferenca_percentual', 0)
            diferenca_absoluta = consumo_kwh - media_6_meses if media_6_meses > 0 else 0
            sistema_fotovoltaico = dados_fatura.get('sistema_fotovoltaico', 'Não')
            
            mensagem_base = f"""A Paz de Deus! 

🟢 CONSUMO MODERADO  

📍 Casa de Oração: {casa_oracao}  
⚡ Instalação ENEL: {numero_instalacao}  
📅 Vencimento: {data_vencimento}  
💰 Valor da Conta: R$ {valor_total:.2f}  

━━━━━━━━━━━━━━━━  
📊 Consumo Atual: {consumo_kwh} kWh  
📉 Média (6 meses): {media_6_meses} kWh  
📉 Redução: {diferenca_absoluta:.0f} kWh ({diferenca_percentual:.1f}%)  """
            
            # Informação sobre fotovoltaico se aplicável
            if sistema_fotovoltaico == 'Sim':
                total_compensacao = dados_fatura.get('total_compensacao', 0)
                mensagem_base += f"""☀️ Economia Fotovoltaica: R$ {total_compensacao:.2f}  """
            
            mensagem = mensagem_base + f"""━━━━━━━━━━━━━━━━  

✅ PARABÉNS:  
🔹 Consumo econômico  
🔹 Uso consciente da energia  
{'🔹 Sistema fotovoltaico otimizando economia  ' if sistema_fotovoltaico == 'Sim' else '🔹 Considere sistema fotovoltaico para mais economia  '}

🤖 Sistema ENEL Automático  
🙏 Deus abençoe!"""

        elif tipo_alerta == "resumo_processamento":
            total_processadas = dados_fatura.get('total_processadas', 0)
            total_faltantes = dados_fatura.get('total_faltantes', 0)
            valor_total_mensal = dados_fatura.get('valor_total_mensal', 0)
            mes_referencia = dados_fatura.get('mes_referencia', datetime.now().strftime("%m/%Y"))
            
            mensagem = f"""A Paz de Deus! 

📊 RESUMO MENSAL ENEL - {mes_referencia}  

━━━━━━━━━━━━━━━━  
📈 Faturas Recebidas: {total_processadas}  
📋 Faturas Pendentes: {total_faltantes}  
💰 Valor Total: R$ {valor_total_mensal:.2f}  
{"✅ Processamento completo  " if total_faltantes == 0 else f"⚠️ {total_faltantes} fatura(s) pendente(s)  "}
━━━━━━━━━━━━━━━━  

🤖 Sistema ENEL Automático  
🙏 Deus abençoe!"""

        else:
            # MENSAGEM PADRÃO - para casos não categorizados
            sistema_fotovoltaico = dados_fatura.get('sistema_fotovoltaico', 'Não')
            
            mensagem_base = f"""A Paz de Deus! 

📍 Casa de Oração: {casa_oracao}  
⚡ Instalação ENEL: {numero_instalacao}  
📅 Vencimento: {data_vencimento}  
💰 Valor da Conta: R$ {valor_total:.2f}  

━━━━━━━━━━━━━━━━  
📊 Consumo Atual: {consumo_kwh} kWh  """
            
            # Informação sobre fotovoltaico se aplicável
            if sistema_fotovoltaico == 'Sim':
                total_compensacao = dados_fatura.get('total_compensacao', 0)
                mensagem_base += f"""☀️ Economia Fotovoltaica: R$ {total_compensacao:.2f}  
✅ Sistema solar funcionando  """
            else:
                mensagem_base += "✅ Consumo dentro do padrão  "
            
            mensagem = mensagem_base + f"""━━━━━━━━━━━━━━━━  

🤖 Sistema ENEL Automático  
🙏 Deus abençoe!"""

        return mensagem
        
    except Exception as e:
        print(f"❌ Erro formatando mensagem ENEL: {e}")
        
        # Mensagem de fallback
        return f"""A Paz de Deus! 

📍 Casa de Oração: {dados_fatura.get('casa_oracao', 'N/A')}  
⚡ Instalação ENEL: {dados_fatura.get('numero_instalacao', 'N/A')}  

━━━━━━━━━━━━━━━━  
⚠️ Erro formatando mensagem de alerta  
━━━━━━━━━━━━━━━━  

🤖 Sistema ENEL Automático  
🙏 Deus abençoe!"""

def formatar_mensagem_teste_enel():
    """
    Mensagem de teste para verificar funcionamento
    """
    agora = datetime.now().strftime("%d/%m/%Y às %H:%M")
    
    return f"""A Paz de Deus! 

🧪 TESTE SISTEMA ENEL  

━━━━━━━━━━━━━━━━  
✅ Telegram Bot funcionando  
✅ Integração Sistema ENEL ativa  
✅ Base CCB Alerta conectada  
✅ Envio de anexos PDF ativo  
✅ Alertas de consumo configurados  
☀️ Análise fotovoltaica ativa  
━━━━━━━━━━━━━━━━  

🔧 Teste realizado em: {agora}  

🤖 Sistema ENEL Automático  
🙏 Deus abençoe!"""

def formatar_mensagem_resumo_duplicatas_enel(estatisticas):
    """
    Formatar mensagem com resumo de duplicatas ENEL
    
    Args:
        estatisticas (dict): Estatísticas de duplicatas
        
    Returns:
        str: Mensagem formatada
    """
    try:
        emails_duplicados = estatisticas.get('emails_duplicados', 0)
        faturas_duplicadas = estatisticas.get('faturas_duplicadas', 0)
        instalacoes_reprocessadas = estatisticas.get('instalacoes_reprocessadas', [])
        
        agora = datetime.now().strftime("%d/%m/%Y às %H:%M")
        
        mensagem = f"""A Paz de Deus! 

📋 CONTROLE DE DUPLICATAS ENEL  

━━━━━━━━━━━━━━━━  
📊 Emails duplicados ignorados: {emails_duplicados}  
📄 Faturas duplicadas ignoradas: {faturas_duplicadas}  
🔄 Instalações reprocessadas: {len(instalacoes_reprocessadas)}  
━━━━━━━━━━━━━━━━  

✅ Sistema funcionando corretamente!  

🤖 Sistema ENEL Automático  
🙏 Deus abençoe!"""
        
        return mensagem
        
    except Exception as e:
        print(f"❌ Erro formatando resumo duplicatas: {e}")
        return f"📋 Resumo de duplicatas ENEL - {datetime.now().strftime('%d/%m/%Y %H:%M')}"

def formatar_mensagem_economia_fotovoltaica(dados_fatura, responsavel_info):
    """
    Mensagem específica para destacar economia com sistema fotovoltaico
    
    Args:
        dados_fatura (dict): Dados da fatura com informações fotovoltaicas
        responsavel_info (dict): Informações do responsável
        
    Returns:
        str: Mensagem formatada focada na economia fotovoltaica
    """
    try:
        casa_oracao = dados_fatura.get('casa_oracao', 'Casa não informada')
        numero_instalacao = dados_fatura.get('numero_instalacao', 'N/A')
        valor_total = dados_fatura.get('valor_total_num', 0)
        data_vencimento = dados_fatura.get('data_vencimento', '')
        
        # Dados fotovoltaicos
        energia_injetada = dados_fatura.get('energia_injetada_num', 0)
        energia_compensada = dados_fatura.get('energia_compensada_num', 0)
        total_compensacao = dados_fatura.get('total_compensacao', 0)
        percentual_economia = dados_fatura.get('percentual_economia_fv', 0)
        valor_sem_fv = dados_fatura.get('valor_integral_sem_fv', 0)
        saldo_creditos = dados_fatura.get('saldo_creditos_num', 0)
        
        mensagem = f"""A Paz de Deus! 

☀️ EXCELENTE ECONOMIA FOTOVOLTAICA  

📍 Casa de Oração: {casa_oracao}  
⚡ Instalação ENEL: {numero_instalacao}  
📅 Vencimento: {data_vencimento}  
💰 Valor da Conta: R$ {valor_total:.2f}  

━━━━━━━━━━━━━━━━  
💵 Economia obtida: R$ {total_compensacao:.2f}  
📈 Percentual: {percentual_economia:.1f}%  
🔌 Sem fotovoltaico seria: R$ {valor_sem_fv:.2f}  
☀️ Energia compensada: {energia_compensada} kWh  
🏦 Saldo de créditos: {saldo_creditos:.1f} kWh  
━━━━━━━━━━━━━━━━  

🎉 PARABÉNS:  
🔹 Sistema fotovoltaico funcionando perfeitamente  
🔹 Economia significativa na conta de luz  
🔹 Contribuindo com o meio ambiente  

🤖 Sistema ENEL Automático  
🙏 Deus abençoe!"""
        
        return mensagem
        
    except Exception as e:
        print(f"❌ Erro formatando mensagem economia fotovoltaica: {e}")
        return "☀️ Erro processando dados de economia fotovoltaica."