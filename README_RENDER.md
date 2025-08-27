# ⚡ Sistema ENEL - Deploy Render

**Versão Web do Sistema ENEL para Deploy no Render**  
*Baseado no projeto BRK funcionando, adaptado para ENEL*

---

## 🚀 **DEPLOY RÁPIDO**

### 1. **Conectar ao GitHub**
```bash
# 1. Push este projeto para seu GitHub
git init
git add .
git commit -m "Sistema ENEL para Render"
git remote add origin https://github.com/SEU_USUARIO/enel-render.git
git push -u origin main
```

### 2. **Configurar no Render Dashboard**
1. Conecte seu repositório GitHub
2. Configure as variáveis de ambiente:

```bash
# OBRIGATÓRIAS
MICROSOFT_CLIENT_ID=seu_client_id_azure
PASTA_ENEL_ID=id_da_pasta_enel_outlook
SECRET_KEY=chave_secreta_flask_qualquer

# OPCIONAIS  
ONEDRIVE_ENEL_ID=id_onedrive_para_planilhas
SENHA_PDF_ENEL=05150
```

### 3. **Deploy Automático**
- Render fará deploy automaticamente
- URL será: `https://seu-app.onrender.com`

---

## 🔧 **COMO USAR**

### **Primeiro Acesso:**
1. Acesse: `https://seu-app.onrender.com`
2. Clique em **"🔑 Upload Token"**
3. Faça upload do `token.json` (gerado localmente)
4. Volte ao Dashboard

### **Processar Faturas:**
1. **"⚡ Processar Faturas"** → Escolher período
2. Sistema fará automaticamente:
   - Download de emails da pasta ENEL
   - Remoção de proteção PDFs (senha 05150)
   - Extração de dados das faturas
   - Geração de planilhas Excel

### **Outras Funções:**
- **"📊 Diagnóstico Pasta"** → Verificar conectividade
- **"📊 Gerar Planilha"** → Consolidar dados existentes
- **"🔐 Remover Proteção"** → Apenas desproteger PDFs

---

## ⚙️ **CONFIGURAÇÃO DETALHADA**

### **Variables de Ambiente Render:**

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `MICROSOFT_CLIENT_ID` | ✅ Sim | Client ID do Azure AD |
| `PASTA_ENEL_ID` | ✅ Sim | ID da pasta ENEL no Outlook |
| `SECRET_KEY` | ✅ Sim | Chave secreta Flask (qualquer string) |
| `ONEDRIVE_ENEL_ID` | ❌ Não | ID pasta OneDrive para salvar planilhas |
| `SENHA_PDF_ENEL` | ❌ Não | Senha PDFs (padrão: 05150) |

### **Como obter PASTA_ENEL_ID:**
1. Use Microsoft Graph Explorer: `https://developer.microsoft.com/graph/graph-explorer`
2. Execute: `GET https://graph.microsoft.com/v1.0/me/mailFolders`  
3. Encontre sua pasta "ENEL" e copie o `id`

---

## 🏗️ **ARQUITETURA**

```
enel-render/
├── app.py                    # 🌐 Servidor Flask principal
├── auth/
│   └── microsoft_auth.py     # 🔐 Autenticação Microsoft Graph
├── processor/
│   ├── email_processor.py    # 📧 Download de emails ENEL
│   └── pdf_processor.py      # 📄 Processamento de PDFs
├── render.yaml               # ⚙️ Configuração deploy
├── requirements.txt          # 📦 Dependências Python
└── README_RENDER.md          # 📖 Este arquivo
```

### **Fluxo de Processamento:**
1. **Microsoft Graph** → Download emails pasta ENEL
2. **PDF Processor** → Remover proteção + extrair dados
3. **Excel Generator** → Consolidar em planilhas
4. **Persistent Storage** → Salvar tudo no Render

---

## 🔒 **SEGURANÇA**

- ✅ **Tokens criptografados** com Fernet
- ✅ **Persistent storage** protegido  
- ✅ **Variáveis ambiente** seguras
- ✅ **HTTPS** automático no Render
- ✅ **Sem dados sensíveis** no código

---

## 📊 **ENDPOINTS DISPONÍVEIS**

| Endpoint | Função |
|----------|--------|
| `/` | Dashboard principal |
| `/upload-token` | Upload seguro token.json |
| `/processar-emails-form` | Interface processamento |
| `/processar-emails-enel` | API processamento |
| `/diagnostico-pasta` | Verificar conectividade |
| `/health` | Health check para monitoramento |

---

## 🐞 **TROUBLESHOOTING**

### **"Token não disponível"**
- Faça upload do token via `/upload-token`
- Verifique se `MICROSOFT_CLIENT_ID` está configurado

### **"Pasta ENEL não encontrada"**
- Verifique se `PASTA_ENEL_ID` está correto
- Use Graph Explorer para encontrar o ID correto

### **"Erro processando PDFs"**
- Verifique se os PDFs estão protegidos com senha "05150"
- Alguns PDFs podem ter formatação diferente

### **Deploy falhando**
- Verifique se todas variáveis obrigatórias estão configuradas
- Logs disponíveis no dashboard do Render

---

## 🔄 **DIFERENÇAS DO SISTEMA DESKTOP**

| Aspecto | Desktop | Render Web |
|---------|---------|------------|
| **Interface** | Tkinter | Flask HTML |
| **Execução** | Manual | Via web |
| **Storage** | Local | Persistent disk |
| **Tokens** | Arquivo local | Criptografado |
| **Deploy** | Anaconda | Automático |
| **Acesso** | Máquina local | Internet |

---

## 💡 **VANTAGENS RENDER**

- ✅ **Acesso remoto** de qualquer lugar
- ✅ **Deploy automático** via Git
- ✅ **Sem instalação** de dependências
- ✅ **Backups automáticos**
- ✅ **HTTPS nativo**
- ✅ **Monitoramento** integrado
- ✅ **Escalável** conforme necessidade

---

## 📞 **SUPORTE**

### **Problemas Comuns:**
1. **First Deploy**: Configure todas variáveis + upload token
2. **Conectividade**: Verifique PASTA_ENEL_ID no Graph Explorer  
3. **Performance**: Plan gratuito tem limites (upgrade se necessário)

### **Logs:**
- Dashboard Render → "Logs" tab
- Logs estruturados para debug fácil

---

**© 2025 - Tesouraria ADM - Sistema ENEL Web**