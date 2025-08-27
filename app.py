#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏢 Sistema ENEL - Versão Web (Render Deploy)
📦 FUNCIONALIDADE: emails → extração → planilhas → renomeação
👨‍💼 AUTOR: Adaptado do sistema BRK para ENEL
🔧 BASEADO EM: brk-render-seguro funcionando
"""

import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, session, render_template
import logging

# Imports dos módulos ENEL
from auth.microsoft_auth import MicrosoftAuth
from processor.sistema_enel import SistemaEnel

# Configuração do Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'enel-dev-key-change-in-production')

# Configuração de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Instâncias globais
auth_manager = MicrosoftAuth()
sistema_enel = SistemaEnel(auth_manager)

# Variáveis de ambiente para ENEL
MICROSOFT_CLIENT_ID = os.getenv('MICROSOFT_CLIENT_ID')
PASTA_ENEL_ID = os.getenv('PASTA_ENEL_ID')
ONEDRIVE_ENEL_ID = os.getenv('ONEDRIVE_ENEL_ID')

# Configuração para logs no Render
os.environ['PYTHONUNBUFFERED'] = '1'

print("🚀 Sistema ENEL web iniciado")
print(f"   📧 Pasta emails: {'configurada' if PASTA_ENEL_ID else 'não configurada'}")
print(f"   📁 OneDrive ENEL: {'configurada' if ONEDRIVE_ENEL_ID else 'não configurada'}")

# ============================================================================
# ROTAS BÁSICAS
# ============================================================================

@app.route('/')
def index():
    """Dashboard ENEL"""
    try:
        if auth_manager.access_token:
            return render_template('dashboard.html')
        else:
            return redirect('/login')
    except Exception as e:
        logger.error(f"Erro na página inicial: {e}")
        return f"Erro: {e}", 500

@app.route('/login')
def login():
    """Login ENEL"""
    try:
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return f"Erro no login: {e}", 500

@app.route('/logout')
def logout():
    """Logout ENEL"""
    try:
        session.clear()
        logger.info("Logout ENEL realizado")
        
        return render_template('logout.html')
    except Exception as e:
        logger.error(f"Erro no logout: {e}")
        return f"Erro no logout: {e}", 500

@app.route('/status')
def status():
    """Status JSON ENEL"""
    try:
        stats = sistema_enel.obter_estatisticas_sistema()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Erro no status: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/criar-estrutura-onedrive', methods=['GET', 'POST'])
def criar_estrutura_onedrive():
    """Criar estrutura de pastas ENEL no OneDrive"""
    if request.method == 'GET':
        return render_template('criar_estrutura.html')
    
    # POST: Criar estrutura
    try:
        resultado = sistema_enel.criar_estrutura_onedrive()
        
        if resultado.get("status") == "sucesso":
            return jsonify(resultado)
        else:
            return jsonify(resultado), 500
            
    except Exception as e:
        logger.error(f"Erro criando estrutura OneDrive: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/test-onedrive', methods=['GET'])
def test_onedrive():
    """Teste de conectividade OneDrive ENEL"""
    try:
        resultado = sistema_enel.testar_onedrive()
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro testando OneDrive: {e}")
        return jsonify({"erro": str(e)}), 500

# ============================================================================
# UPLOAD DE TOKEN (BASEADO NO BRK)
# ============================================================================

@app.route('/upload-token', methods=['GET', 'POST'])
def upload_token():
    """Upload seguro de token.json"""
    if request.method == 'GET':
        return render_template('upload_token.html')
    
    # POST: Processar upload
    try:
        if 'token_file' not in request.files:
            return jsonify({"erro": "Nenhum arquivo enviado"}), 400
        
        file = request.files['token_file']
        if file.filename == '':
            return jsonify({"erro": "Nenhum arquivo selecionado"}), 400
        
        # Validar conteúdo JSON
        try:
            token_data = json.loads(file.read().decode('utf-8'))
            
            # Validar campos obrigatórios
            required_fields = ['access_token', 'refresh_token']
            for field in required_fields:
                if field not in token_data:
                    return jsonify({"erro": f"Campo obrigatório ausente: {field}"}), 400
            
            # Salvar tokens no auth_manager
            auth_manager.access_token = token_data['access_token']
            auth_manager.refresh_token = token_data['refresh_token']
            
            # Salvar de forma segura e criptografada
            sucesso = auth_manager.salvar_token_persistent()
            
            if sucesso:
                logger.info("Token ENEL carregado via upload")
                return jsonify({
                    "status": "sucesso",
                    "mensagem": "Token carregado e criptografado com sucesso!",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify({"erro": "Falha ao salvar token"}), 500
                
        except json.JSONDecodeError:
            return jsonify({"erro": "Arquivo não é um JSON válido"}), 400
            
    except Exception as e:
        logger.error(f"Erro no upload de token: {e}")
        return jsonify({"erro": f"Erro no upload: {str(e)}"}), 500

# ============================================================================
# FUNCIONALIDADES ENEL
# ============================================================================

@app.route('/diagnostico-pasta', methods=['GET'])
def diagnostico_pasta():
    """Diagnóstico da pasta ENEL"""
    try:
        resultado = sistema_enel.diagnosticar_pasta_enel()
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro no diagnóstico: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/processar-emails-form', methods=['GET'])
def processar_emails_form():
    """Formulário para processar emails ENEL"""
    try:
        if not auth_manager.access_token:
            return redirect('/login')
        
        return render_template('processar_emails.html')
    except Exception as e:
        logger.error(f"Erro no formulário: {e}")
        return f"Erro: {e}", 500

@app.route('/processar-emails-enel', methods=['POST'])
def processar_emails_enel():
    """Processar emails ENEL - funcionalidade principal INCREMENTAL"""
    try:
        dados_request = request.get_json() or {}
        
        resultado = sistema_enel.processar_modo_hibrido(dados_request)
        
        if resultado.get("status") == "sucesso":
            return jsonify(resultado)
        elif "erro" in resultado:
            return jsonify(resultado), 500
        else:
            return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro processamento ENEL: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/status-controle-mensal', methods=['GET'])
def status_controle_mensal():
    """Obter status do controle mensal ENEL"""
    try:
        resultado = sistema_enel.obter_status_controle_mensal()
        
        if "erro" in resultado:
            return jsonify(resultado), 404
        else:
            return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro obtendo status controle: {e}")
        return jsonify({"erro": str(e)}), 500

# ============================================================================
# SISTEMA DE ALERTAS ENEL
# ============================================================================

@app.route('/alertas-form', methods=['GET'])
def alertas_form():
    """Formulário para sistema de alertas ENEL"""
    try:
        if not auth_manager.access_token:
            return redirect('/login')
        
        return render_template('alertas.html')
    except Exception as e:
        logger.error(f"Erro no formulário alertas: {e}")
        return f"Erro: {e}", 500

@app.route('/testar-alertas', methods=['POST'])
def testar_alertas():
    """Testar sistema de alertas ENEL"""
    try:
        resultado = sistema_enel.testar_sistema_alertas()
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro testando alertas: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/processar-alertas-consumo', methods=['POST'])
def processar_alertas_consumo():
    """Processar alertas de consumo alto"""
    try:
        dados_request = request.get_json() or {}
        limite_percentual = dados_request.get('limite_percentual', 150)
        
        resultado = sistema_enel.processar_alertas_consumo_alto(limite_percentual)
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro processando alertas consumo: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/enviar-resumo-mensal', methods=['POST'])
def enviar_resumo_mensal():
    """Enviar resumo mensal para administradores"""
    try:
        resultado = sistema_enel.enviar_resumo_mensal_admin()
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro enviando resumo mensal: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check para Render"""
    try:
        status = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "sistema": "ENEL Render Web",
            "componentes": {
                "flask": "ok",
                "auth": "ok" if auth_manager else "error",
                "processamento": "ativo"
            }
        }
        
        if auth_manager.access_token:
            status["componentes"]["token"] = "disponivel"
        else:
            status["componentes"]["token"] = "nao_disponivel"
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "erro": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# ============================================================================
# TRATAMENTO DE ERROS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Página 404"""
    return jsonify({
        "erro": "Endpoint não encontrado",
        "sistema": "ENEL Render Web",
        "endpoints_disponiveis": [
            "/", "/login", "/logout", "/status", "/upload-token",
            "/diagnostico-pasta", "/processar-emails-form", "/processar-emails-enel",
            "/health"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Tratamento de erros 500"""
    logger.error(f"Erro interno: {error}")
    return jsonify({
        "erro": "Erro interno do servidor",
        "sistema": "ENEL Render Web",
        "timestamp": datetime.now().isoformat()
    }), 500

# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

def verificar_configuracao():
    """Verifica configurações básicas"""
    variaveis_obrigatorias = ['MICROSOFT_CLIENT_ID', 'PASTA_ENEL_ID']
    
    missing = [var for var in variaveis_obrigatorias if not os.getenv(var)]
    
    if missing:
        print(f"❌ ERRO: Variáveis não configuradas: {', '.join(missing)}")
        print("⚠️ Configure no Render Dashboard ou use upload de token")
        return False
    
    print(f"✅ Configuração básica OK")
    return True

def inicializar_aplicacao():
    """Inicialização do sistema ENEL"""
    print(f"\n🚀 INICIANDO SISTEMA ENEL RENDER WEB")
    print(f"="*60)
    
    # Verificar configuração (não crítico - pode usar upload)
    config_ok = verificar_configuracao()
    if not config_ok:
        print("⚠️ Configuração incompleta - use /upload-token")
    
    if auth_manager.access_token:
        print(f"✅ Autenticação ENEL funcionando")
    else:
        print(f"⚠️ Token não encontrado - use /upload-token")
    
    print(f"✅ Sistema ENEL web inicializado!")
    print(f"   📧 Processamento de emails ENEL")
    print(f"   📄 Processamento de PDFs com senha")
    print(f"   📊 Geração de planilhas organizadas")
    print(f"   🌐 Interface web completa")
    print(f"   🔒 Tokens criptografados")
    
    return True

# ============================================================================
# PONTO DE ENTRADA
# ============================================================================

if __name__ == '__main__':
    if inicializar_aplicacao():
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('FLASK_ENV') == 'development'
        
        print(f"🌐 Servidor ENEL iniciando na porta {port}")
        print(f"📱 Sistema web funcionando!")
        print(f"🔧 Dashboard disponível em /")
        
        app.run(host='0.0.0.0', port=port, debug=debug)
    else:
        print(f"❌ Falha na inicialização")
        exit(1)