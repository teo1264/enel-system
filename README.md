# 🏢 Sistema ENEL - Versão Web (Render Deploy)

Sistema automatizado para processamento de faturas ENEL com interface web completa, desenvolvido especificamente para deploy na nuvem.

## ⚡ O que faz o Sistema

O **Sistema ENEL Web** automatiza completamente o processamento de faturas de energia elétrica:

### 📋 **Dados Extraídos de Cada Fatura**
- 🏠 **Número da Instalação**: Identificação única ENEL
- 📄 **Nota Fiscal**: Número do documento fiscal
- 📅 **Data de Emissão**: Quando a fatura foi gerada
- 📅 **Data de Vencimento**: Prazo para pagamento
- 💰 **Valor Total**: Quantia a ser paga
- ⚡ **Consumo kWh**: Energia consumida no período
- 📆 **Competência**: Mês/ano de referência

### 🌞 **Energia Fotovoltaica (Solar)**
- ☀️ **Sistema Fotovoltaico**: Detecta automaticamente se tem painel solar
- 💸 **Compensação TUSD**: Desconto TUSD por energia injetada
- 💸 **Compensação TE**: Desconto TE por energia injetada  
- 💰 **Total Compensação**: Soma das compensações solares
- 📊 **Valor Integral**: Valor sem desconto solar (real gasto)
- 📈 **Percentual Economia**: % de economia com energia solar

### 📧 **Processamento Automático**
- **Download** automático de emails da pasta ENEL
- **Remoção** de proteção PDF (senha 05150)
- **Extração** completa de dados das faturas
- **Geração** de planilhas Excel organizadas
- **Renomeação inteligente** baseada no vencimento para integração SIGA

### 🚨 **Sistema de Alertas**
- **Alertas** de faturas pendentes via Telegram
- **Notificações** de consumo elevado automático
- **Resumos** mensais para administradores
- **Envio** de PDFs anexados nas mensagens
- **Integração** com base CCB Alerta Bot

### 🌐 **Interface Web Completa**
- **Dashboard** responsivo com status em tempo real
- **Formulários** para configuração e processamento
- **Upload** seguro de tokens de autenticação
- **Monitoramento** de estrutura OneDrive
- **Deploy** automático no Render

## 🚀 Deploy no Render

### **Configuração Automática**
```yaml
# render.yaml já configurado
startCommand: python app.py
buildCommand: pip install -r requirements.txt
```

### **Variáveis de Ambiente Necessárias**
```bash
MICROSOFT_CLIENT_ID=seu_client_id
PASTA_ENEL_ID=id_da_pasta_emails
ONEDRIVE_ENEL_ID=id_pasta_onedrive

# Para Sistema de Alertas
TELEGRAM_BOT_TOKEN=token_do_bot
ONEDRIVE_ALERTA_ID=id_base_ccb
# NOTA: ADMIN_IDS foi migrado para busca dinâmica na base CCB Alerta (alertas_bot.db)
```

## 📦 Instalação Local (Desenvolvimento)

```bash
# Clone o repositório
git clone [url-do-repositorio]
cd enel

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente ou use upload de token
cp .env.example .env

# Execute o sistema
python app.py
```

## 🔧 Funcionalidades Principais

### **📊 Dashboard Principal**
- Status do sistema em tempo real
- Estatísticas de processamento
- Acesso a todas funcionalidades

### **⚡ Processamento de Faturas**
- Seleção de período (1 dia a 1 mês)
- Processamento incremental otimizado
- Relatórios detalhados de resultados

### **🚨 Sistema de Alertas**
- Configuração de limites de consumo
- Testes do sistema completo
- Envio manual de resumos

### **🔑 Gerenciamento de Tokens**
- Upload seguro de tokens Microsoft
- Criptografia automática
- Validação de credenciais

## 🗂️ Estrutura do Projeto

```
E:\enel\
├── app.py                  # 🌐 Aplicação Flask principal
├── auth/                   # 🔐 Autenticação Microsoft
├── processor/              # ⚙️ Lógica de processamento
│   ├── sistema_enel.py     # 📊 Orquestrador principal
│   ├── email_processor.py  # 📧 Processamento de emails
│   ├── pdf_processor.py    # 📄 Processamento de PDFs
│   ├── planilha_manager.py # 📈 Geração de planilhas
│   ├── onedrive_manager.py # 💾 Integração OneDrive
│   └── alertas/            # 🚨 Sistema de alertas
├── templates/              # 🎨 Interface web
├── static/                 # 🎯 CSS e JavaScript
├── requirements.txt        # 📦 Dependências
├── render.yaml             # 🚀 Configuração deploy
└── runtime.txt             # 🐍 Versão Python
```

## ⚙️ Tecnologias Utilizadas

- **Backend**: Python 3.11, Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **APIs**: Microsoft Graph API, Telegram Bot API
- **Processamento**: PyPDF2, pdfplumber, openpyxl
- **Deploy**: Render (automático via GitHub)
- **Autenticação**: OAuth2 Microsoft
- **Storage**: OneDrive integração

## 📱 Acesso ao Sistema

### **Produção (Render)**
- URL será fornecida após deploy
- Interface web completa
- Todos recursos disponíveis

### **Desenvolvimento Local**
```bash
python app.py
# Acesse: http://localhost:5000
```

## 🔒 Segurança

- **Tokens criptografados** no persistent storage
- **Variáveis de ambiente** para credenciais
- **Validação** de arquivos de upload
- **Logs** detalhados para auditoria

## 📋 Notas Importantes

### **Para Tesouraria ADM**
- Sistema baseado no sistema desktop já em uso
- **Migração para nuvem** mantendo todas funcionalidades
- **Acesso remoto** de qualquer dispositivo
- **Backup automático** via Render

### **Diferenças da Versão Desktop**
- **Interface web** ao invés de Tkinter
- **Deploy na nuvem** ao invés de instalação local  
- **Acesso compartilhado** ao invés de uso individual
- **Armazenamento persistente** na nuvem

## 🆘 Suporte

Para dúvidas ou problemas:
1. Verificar logs no dashboard Render
2. Testar conectividade OneDrive
3. Validar configuração de variáveis de ambiente
4. Verificar status do sistema via `/status`

---

**🏢 Sistema ENEL Web - Tesouraria ADM**  
**📧 Processamento automático • 🚨 Alertas inteligentes • 🌐 Interface moderna**