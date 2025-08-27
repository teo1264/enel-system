#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 CLASSIFICADOR DE CONSUMO ENEL - Função Central Unificada
🎯 FUNÇÃO: Determinar tipo de alerta baseado no escalonamento de consumo
👨‍💼 AUTOR: Sistema unificado ENEL
🔧 DESCRIÇÃO: Uma única fonte de verdade para classificação de consumo
📋 USO: Tanto para planilha quanto para mensagens de alerta

LÓGICA DE ESCALONAMENTO (CORRIGIDA):
- 🔴 CRÍTICO: > 150% da média
- 🟠 ALTO: 100% - 150% da média  
- 🟡 ACIMA DA MÉDIA: 50% - 100% da média
- 🟢 MODERADO: < 50% da média
"""

def determinar_tipo_alerta_consumo(consumo_atual, media_6_meses):
    """
    FUNÇÃO CENTRAL UNIFICADA - Determinar tipo de alerta baseado no consumo
    
    Esta função é a ÚNICA fonte de verdade para classificação de consumo.
    Deve ser usada tanto na planilha quanto nas mensagens de alerta.
    
    Args:
        consumo_atual (float): Consumo atual em kWh
        media_6_meses (float): Média dos últimos 6 meses em kWh
        
    Returns:
        dict: {
            'tipo_alerta': str,           # Tipo do alerta para mensagem
            'classificacao': str,         # Classificação para planilha  
            'porcentagem_consumo': float, # Percentual em relação à média
            'diferenca_percentual': float,# Diferença percentual
            'diferenca_absoluta': float,  # Diferença absoluta em kWh
            'status_cor': str            # Código de cor para interface
        }
    """
    try:
        # Validações básicas
        if not consumo_atual or consumo_atual <= 0:
            return {
                'tipo_alerta': 'sem_dados',
                'classificacao': 'Sem Dados',
                'porcentagem_consumo': 0.0,
                'diferenca_percentual': 0.0,
                'diferenca_absoluta': 0.0,
                'status_cor': 'cinza'
            }
        
        if not media_6_meses or media_6_meses <= 0:
            return {
                'tipo_alerta': 'sem_historico',
                'classificacao': 'Sem Histórico',
                'porcentagem_consumo': 100.0,
                'diferenca_percentual': 0.0,
                'diferenca_absoluta': 0.0,
                'status_cor': 'cinza'
            }
        
        # Cálculos principais
        porcentagem_consumo = (consumo_atual / media_6_meses) * 100
        diferenca_percentual = ((consumo_atual - media_6_meses) / media_6_meses) * 100
        diferenca_absoluta = consumo_atual - media_6_meses
        
        # LÓGICA DE ESCALONAMENTO UNIFICADA (CORRIGIDA)
        if porcentagem_consumo > 150:
            # CRÍTICO: > 150% da média
            resultado = {
                'tipo_alerta': 'consumo_critico',
                'classificacao': 'Crítico',
                'porcentagem_consumo': porcentagem_consumo,
                'diferenca_percentual': diferenca_percentual,
                'diferenca_absoluta': diferenca_absoluta,
                'status_cor': 'vermelho'
            }
        elif 100 <= porcentagem_consumo <= 150:
            # ALTO: 100% - 150% da média
            resultado = {
                'tipo_alerta': 'consumo_alto',
                'classificacao': 'Alto',
                'porcentagem_consumo': porcentagem_consumo,
                'diferenca_percentual': diferenca_percentual,
                'diferenca_absoluta': diferenca_absoluta,
                'status_cor': 'laranja'
            }
        elif 50 <= porcentagem_consumo < 100:
            # ACIMA DA MÉDIA: 50% - 100% da média
            resultado = {
                'tipo_alerta': 'consumo_acima_media',
                'classificacao': 'Acima da Média',
                'porcentagem_consumo': porcentagem_consumo,
                'diferenca_percentual': diferenca_percentual,
                'diferenca_absoluta': diferenca_absoluta,
                'status_cor': 'amarelo'
            }
        elif porcentagem_consumo < 50:
            # MODERADO: < 50% da média
            resultado = {
                'tipo_alerta': 'consumo_moderado',
                'classificacao': 'Moderado',
                'porcentagem_consumo': porcentagem_consumo,
                'diferenca_percentual': diferenca_percentual,
                'diferenca_absoluta': diferenca_absoluta,
                'status_cor': 'verde'
            }
        else:
            # Fallback - não deveria chegar aqui
            resultado = {
                'tipo_alerta': 'consumo_normal',
                'classificacao': 'Normal',
                'porcentagem_consumo': porcentagem_consumo,
                'diferenca_percentual': diferenca_percentual,
                'diferenca_absoluta': diferenca_absoluta,
                'status_cor': 'azul'
            }
        
        # Log para debug (pode ser removido em produção)
        print(f"🔍 Classificação: {consumo_atual} kWh vs {media_6_meses} kWh média")
        print(f"   📊 Percentual: {porcentagem_consumo:.1f}% → {resultado['classificacao']}")
        print(f"   📈 Diferença: {diferenca_absoluta:.0f} kWh ({diferenca_percentual:.1f}%)")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro na classificação de consumo: {e}")
        return {
            'tipo_alerta': 'erro',
            'classificacao': 'Erro',
            'porcentagem_consumo': 0.0,
            'diferenca_percentual': 0.0,
            'diferenca_absoluta': 0.0,
            'status_cor': 'cinza'
        }

def obter_detalhes_classificacao(tipo_alerta):
    """
    Obter detalhes adicionais sobre cada tipo de classificação
    
    Args:
        tipo_alerta (str): Tipo do alerta
        
    Returns:
        dict: Detalhes da classificação
    """
    detalhes = {
        'consumo_critico': {
            'emoji': '🔴',
            'titulo': 'CONSUMO CRÍTICO',
            'descricao': 'Consumo muito acima da média (>150%)',
            'acoes': [
                'Verificar ar condicionado (principal causa)',
                'Confirmar se equipamentos foram desligados',
                'Investigar uso excessivo de energia'
            ],
            'urgencia': 'alta'
        },
        'consumo_alto': {
            'emoji': '🟠',
            'titulo': 'CONSUMO ALTO',
            'descricao': 'Consumo bem acima da média (100-150%)',
            'acoes': [
                'Ar condicionado pode ter ficado ligado',
                'Verificar equipamentos elétricos',
                'Monitorar próximas faturas'
            ],
            'urgencia': 'media'
        },
        'consumo_acima_media': {
            'emoji': '🟡',
            'titulo': 'CONSUMO ACIMA DA MÉDIA',
            'descricao': 'Consumo moderadamente elevado (50-100%)',
            'acoes': [
                'Aumento dentro do aceitável',
                'Monitorar próximas faturas',
                'Verificar se foi uso pontual'
            ],
            'urgencia': 'baixa'
        },
        'consumo_moderado': {
            'emoji': '🟢',
            'titulo': 'CONSUMO MODERADO',
            'descricao': 'Consumo econômico (<50%)',
            'acoes': [
                'Consumo econômico',
                'Uso consciente da energia',
                'Manter padrão atual'
            ],
            'urgencia': 'nenhuma'
        }
    }
    
    return detalhes.get(tipo_alerta, {
        'emoji': '⚪',
        'titulo': 'CONSUMO NORMAL',
        'descricao': 'Consumo dentro do padrão esperado',
        'acoes': ['Consumo normal'],
        'urgencia': 'nenhuma'
    })

def validar_dados_consumo(consumo_atual, media_6_meses, historico_consumo=None):
    """
    Validar dados de consumo antes da classificação
    
    Args:
        consumo_atual (float): Consumo atual
        media_6_meses (float): Média 6 meses
        historico_consumo (list, optional): Histórico completo
        
    Returns:
        dict: Status da validação
    """
    problemas = []
    
    if not consumo_atual or consumo_atual <= 0:
        problemas.append("Consumo atual inválido ou zero")
    
    if not media_6_meses or media_6_meses <= 0:
        problemas.append("Média histórica inválida ou zero")
    
    if historico_consumo and len(historico_consumo) < 2:
        problemas.append("Histórico insuficiente para análise confiável")
    
    if consumo_atual and media_6_meses:
        porcentagem = (consumo_atual / media_6_meses) * 100
        if porcentagem > 1000:  # > 1000% pode ser erro de dados
            problemas.append("Consumo excessivamente alto - verificar dados")
    
    return {
        'valido': len(problemas) == 0,
        'problemas': problemas,
        'confiabilidade': 'alta' if len(problemas) == 0 else 'baixa'
    }

# Função de compatibilidade com código legado
def determinar_alerta_consumo_legacy(porcentagem_consumo):
    """
    Compatibilidade com código legado que usa porcentagem diretamente
    
    Args:
        porcentagem_consumo (float): Porcentagem do consumo em relação à média
        
    Returns:
        str: Classificação legado
    """
    if porcentagem_consumo > 150:
        return 'Crítico'
    elif 100 <= porcentagem_consumo <= 150:
        return 'Alto'
    elif 50 <= porcentagem_consumo < 100:
        return 'Acima da Média'
    elif porcentagem_consumo < 50:
        return 'Moderado'
    else:
        return 'Normal'