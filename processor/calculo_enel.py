#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧮 MÓDULO CENTRALIZADO - CÁLCULOS ENEL
📊 FUNÇÃO: Função única para todos os cálculos de média e diferença percentual
🎯 OBJETIVO: Evitar discrepâncias entre planilha e alertas
👨‍💼 AUTOR: Centralização para manutenção única
"""

def calcular_media_e_diferenca_enel(historico_consumo):
    """
    FUNÇÃO CENTRALIZADA - Cálculo de média e diferença percentual ENEL
    
    Esta função deve ser usada por:
    1. Geração de planilhas (src/pdf/processor.py)  
    2. Sistema de alertas (processor/alertas/alert_processor.py)
    3. Qualquer outro local que precise desses cálculos
    
    FÓRMULA OFICIAL ENEL:
    1. Histórico ordenado por data (mais recente primeiro)
    2. Consumo atual = primeiro registro
    3. Média dos 6 meses ANTERIORES (excluindo atual)
    4. Diferença percentual = ((atual - média) / média * 100)
    
    Args:
        historico_consumo (list): Lista ordenada por data DESC
                                 [{"mes_ano": "12/2024", "consumo": 850, "tipo": "ATUAL"}, ...]
        
    Returns:
        tuple: (consumo_atual, media_6_meses, diferenca_percentual)
               (float, float, float)
    """
    try:
        if not historico_consumo or len(historico_consumo) < 1:
            return 0, 0, 0
        
        # 1. Consumo atual (primeiro da lista, mais recente)
        consumo_atual = float(historico_consumo[0].get("consumo", 0))
        
        if len(historico_consumo) < 2:
            # Só tem o registro atual, não há histórico para média
            return consumo_atual, 0, 0
        
        # 2. Últimos 6 meses ANTERIORES (excluindo o atual)
        # Pega do índice 1 até 7 (máximo 6 registros)
        ultimos_6_meses = historico_consumo[1:7] if len(historico_consumo) >= 7 else historico_consumo[1:]
        
        if not ultimos_6_meses:
            return consumo_atual, 0, 0
        
        # 3. Calcular média simples dos 6 meses anteriores
        consumos_6_meses = []
        for item in ultimos_6_meses:
            try:
                consumo = float(item.get("consumo", 0))
                if consumo > 0:  # Só considerar consumos válidos
                    consumos_6_meses.append(consumo)
            except (ValueError, TypeError):
                continue
        
        if not consumos_6_meses:
            return consumo_atual, 0, 0
        
        media_6_meses = sum(consumos_6_meses) / len(consumos_6_meses)
        
        # 4. Calcular diferença percentual
        if media_6_meses > 0 and consumo_atual is not None:
            diferenca_percentual = ((consumo_atual - media_6_meses) / media_6_meses * 100)
        else:
            diferenca_percentual = 0
        
        # Debug opcional (comentar em producao)
        print(f"Calculo ENEL centralizado:")
        print(f"   Consumo atual: {consumo_atual:.2f} kWh")
        print(f"   Media 6 meses: {media_6_meses:.2f} kWh ({len(consumos_6_meses)} registros validos)")
        print(f"   Diferenca: {diferenca_percentual:+.1f}%")
        
        return consumo_atual, media_6_meses, diferenca_percentual
        
    except Exception as e:
        print(f"ERRO no calculo centralizado ENEL: {e}")
        return 0, 0, 0

def validar_historico_consumo(historico_consumo):
    """
    Validar formato do histórico de consumo
    
    Args:
        historico_consumo (list): Histórico para validar
        
    Returns:
        bool: True se formato está correto
    """
    try:
        if not isinstance(historico_consumo, list):
            return False
        
        if len(historico_consumo) < 1:
            return False
        
        # Verificar se primeiro item tem os campos necessários
        primeiro_item = historico_consumo[0]
        if not isinstance(primeiro_item, dict):
            return False
        
        if "consumo" not in primeiro_item:
            return False
        
        # Tentar converter consumo para float
        try:
            float(primeiro_item["consumo"])
        except (ValueError, TypeError):
            return False
        
        return True
        
    except Exception:
        return False

# Função de compatibilidade (wrapper) para não quebrar código existente
def calcular_media_consumo_enel(historico_consumo):
    """
    WRAPPER: Manter compatibilidade com código existente
    Redireciona para a função centralizada
    """
    return calcular_media_e_diferenca_enel(historico_consumo)