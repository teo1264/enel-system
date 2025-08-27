# 🧮 CENTRALIZAÇÃO DOS CÁLCULOS ENEL

## ⚠️ PROBLEMA IDENTIFICADO

**SITUAÇÃO ATUAL PERIGOSA:**
- Cálculos **duplicados** em 2 lugares diferentes
- Risco de **discrepâncias** entre planilha e alertas  
- **Manutenção duplicada** propensa a erros

### **Locais com Cálculo Duplicado:**

1. **Geração de Planilhas:** `src/pdf/processor.py` - linha ~XXX
   ```python
   media_6_meses = sum(item["consumo"] for item in ultimos_6_meses) / len(ultimos_6_meses)
   diferenca_percentual = ((consumo_atual - media_6_meses) / media_6_meses * 100)
   ```

2. **Sistema de Alertas:** `processor/alertas/alert_processor.py` - linha ~XXX  
   ```python
   media_6_meses = sum(consumos_6_meses) / len(consumos_6_meses)
   diferenca_percentual = ((consumo_atual - media_6_meses) / media_6_meses * 100)
   ```

## ✅ SOLUÇÃO IMPLEMENTADA

### **Função Centralizada:** `processor/calculo_enel.py`

```python
def calcular_media_e_diferenca_enel(historico_consumo):
    """
    FUNÇÃO ÚNICA para todos os cálculos ENEL
    - Usada por planilhas E alertas
    - Mantém consistência total
    - Manutenção em um só lugar
    """
    # Lógica única e centralizada
    return consumo_atual, media_6_meses, diferenca_percentual
```

## 🔧 MODIFICAÇÕES NECESSÁRIAS

### **1. Atualizar Geração de Planilhas:**
```python
# EM: src/pdf/processor.py
# TROCAR:
media_6_meses = sum(item["consumo"] for item in ultimos_6_meses) / len(ultimos_6_meses)
diferenca_percentual = ((consumo_atual - media_6_meses) / media_6_meses * 100)

# POR:
from processor.calculo_enel import calcular_media_e_diferenca_enel
consumo_atual, media_6_meses, diferenca_percentual = calcular_media_e_diferenca_enel(historico_consumo)
```

### **2. Atualizar Sistema de Alertas:**
```python  
# EM: processor/alertas/alert_processor.py
# TROCAR:
media_6_meses = sum(consumos_6_meses) / len(consumos_6_meses)
diferenca_percentual = ((consumo_atual - media_6_meses) / media_6_meses * 100)

# POR:
from processor.calculo_enel import calcular_media_e_diferenca_enel
consumo_atual, media_6_meses, diferenca_percentual = calcular_media_e_diferenca_enel(historico_consumo)
```

## 🎯 BENEFÍCIOS

### **✅ Consistência Total:**
- Planilha e alertas **sempre** com mesmo resultado
- Impossível ter discrepâncias

### **✅ Manutenção Única:**
- Alterar fórmula em **1 lugar só**
- Mudança se aplica automaticamente a tudo

### **✅ Facilidade de Teste:**
- Testar cálculo uma vez
- Validação centralizada

### **✅ Rastreabilidade:**
- Debug em local único
- Logs centralizados

## ⚡ STATUS DE IMPLEMENTAÇÃO

- [x] **Função centralizada criada**
- [ ] **Integrar na geração de planilhas** 
- [ ] **Integrar no sistema de alertas**
- [ ] **Remover código duplicado**
- [ ] **Testar consistency**

## 🧪 COMO TESTAR

```python
from processor.calculo_enel import calcular_media_e_diferenca_enel

# Histórico de teste
historico = [
    {"mes_ano": "12/2024", "consumo": 850},  # Atual
    {"mes_ano": "11/2024", "consumo": 420},  # 6 meses
    {"mes_ano": "10/2024", "consumo": 380},  # anteriores
    # ... mais registros
]

# Teste único
atual, media, diferenca = calcular_media_e_diferenca_enel(historico)
print(f"Resultado: {atual} kWh, média {media:.2f} kWh, diferença {diferenca:+.1f}%")
```

## 🎯 CONCLUSÃO

**Com essa centralização:**
- ✅ **Zero risco** de discrepâncias
- ✅ **Manutenção única** da fórmula ENEL
- ✅ **Consistência** entre planilha e alertas  
- ✅ **Facilidade** para ajustes futuros

**Pronto para implementar as integrações!**