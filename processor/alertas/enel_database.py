#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗃️ ENEL DATABASE - Acesso Base CCB Alerta Bot via OneDrive  
📧 FUNÇÃO: Consultar responsáveis por casa de oração ENEL
👨‍💼 RESPONSÁVEL: Sistema ENEL baseado no BRK
📅 DATA CRIAÇÃO: Baseado no ccb_database.py BRK
📁 ESTRUTURA: Casa ENEL → Código BRK → Responsáveis CCB
✅ APROVEITAMENTO: Mesma base alertas_bot.db do BRK
"""

import os
import sqlite3
import requests
import tempfile
from auth.microsoft_auth import MicrosoftAuth

def extrair_codigo_ccb_da_casa_enel(casa_enel_completa):
    """
    Extrair código CCB da casa ENEL
    
    Exemplos:
    "BR 21-0270 - CENTRO" → "BR 21-0270"
    "ADM – MAUA – SP" → "ADM"
    "BR 21-0271 - JARDIM PRIMAVERA" → "BR 21-0271"
    
    Args:
        casa_enel_completa (str): Nome completo da casa ENEL
        
    Returns:
        str: Código CCB ou casa original se não encontrar padrão
    """
    try:
        if not casa_enel_completa:
            return ""
            
        casa_str = str(casa_enel_completa).strip()
        
        # Padrão: "BR XX-XXXX - NOME" → "BR XX-XXXX"  
        if " - " in casa_str and casa_str.startswith("BR "):
            codigo = casa_str.split(" - ")[0].strip()
            print(f"🔍 Código extraído: '{casa_enel_completa}' → '{codigo}'")
            return codigo
        
        # Caso especial: ADM, SEDE, etc.
        if any(palavra in casa_str.upper() for palavra in ["ADM", "SEDE", "ADMIN"]):
            codigo = casa_str.split()[0].upper()  # Primeira palavra
            print(f"🔍 Código administrativo: '{casa_enel_completa}' → '{codigo}'")
            return codigo
            
        # Se não encontrar padrão, usar a casa completa
        print(f"⚠️ Padrão não reconhecido, usando casa completa: '{casa_enel_completa}'")
        return casa_str
        
    except Exception as e:
        print(f"❌ Erro extraindo código da casa '{casa_enel_completa}': {e}")
        return str(casa_enel_completa) if casa_enel_completa else ""

def obter_responsaveis_por_casa_enel(casa_enel):
    """
    Consultar responsáveis na base CCB por casa ENEL
    
    Fluxo:
    1. Casa ENEL → Extrair código BRK  
    2. Código BRK → Buscar na base CCB
    3. Retornar responsáveis Telegram
    
    Args:
        casa_enel (str): Casa ENEL (ex: "BR 21-0270 - CENTRO")
    
    Returns:
        list: Lista de responsáveis [{'user_id': int, 'nome': str, 'funcao': str}]
    """
    try:
        print(f"🔍 Consultando responsáveis ENEL para: {casa_enel}")
        
        # 1. Extrair código BRK da casa ENEL
        codigo_ccb = extrair_codigo_ccb_da_casa_enel(casa_enel)
        if not codigo_ccb:
            print(f"❌ Não foi possível extrair código da casa: {casa_enel}")
            return []
            
        print(f"🎯 Código CCB extraído: {codigo_ccb}")
        
        # 2. Verificar variável ambiente (mesma do BRK)
        onedrive_alerta_id = os.getenv("ONEDRIVE_ALERTA_ID")
        if not onedrive_alerta_id:
            print(f"❌ ONEDRIVE_ALERTA_ID não configurado")
            return []
        
        print(f"📁 OneDrive Alerta ID: {onedrive_alerta_id[:20]}...")
        
        # 3. Usar auth Microsoft (mesma instância do BRK)
        auth_manager = MicrosoftAuth()
        if not auth_manager.access_token:
            print(f"❌ Auth Microsoft não disponível")
            return []
        
        print(f"🔐 Auth Microsoft: ✅ Disponível")
        
        # 4. Obter headers autenticados
        headers = auth_manager.obter_headers_autenticados()
        if not headers:
            print(f"❌ Headers de autenticação não disponíveis")
            return []
        
        # 5. Buscar database alertas_bot.db na pasta /Alerta/ (mesma do BRK)
        print(f"☁️ Buscando alertas_bot.db na pasta /Alerta/...")
        
        # Listar arquivos na pasta /Alerta/
        url = f"https://graph.microsoft.com/v1.0/me/drive/items/{onedrive_alerta_id}/children"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Erro acessando pasta /Alerta/: HTTP {response.status_code}")
            return []
        
        arquivos = response.json().get('value', [])
        
        # Procurar alertas_bot.db
        db_file_id = None
        for arquivo in arquivos:
            if arquivo.get('name', '').lower() == 'alertas_bot.db':
                db_file_id = arquivo['id']
                print(f"💾 alertas_bot.db encontrado: {arquivo['name']}")
                break
        
        if not db_file_id:
            print(f"❌ alertas_bot.db não encontrado na pasta /Alerta/")
            return []
        
        # 6. Baixar database para cache temporário
        print(f"📥 Baixando alertas_bot.db...")
        
        download_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{db_file_id}/content"
        download_response = requests.get(download_url, headers=headers, timeout=60)
        
        if download_response.status_code != 200:
            print(f"❌ Erro baixando database: HTTP {download_response.status_code}")
            return []
        
        # Salvar em cache local temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db', prefix='enel_cache_') as tmp_file:
            tmp_file.write(download_response.content)
            db_path = tmp_file.name
        
        print(f"💾 Database baixado para: {db_path}")
        
        # 7. Conectar SQLite e consultar responsáveis (mesma tabela BRK)
        conn = sqlite3.connect(db_path)
        
        try:
            responsaveis = conn.execute("""
                SELECT user_id, nome, funcao 
                FROM responsaveis 
                WHERE codigo_casa = ?
            """, (codigo_ccb,)).fetchall()
            
            # 8. Formatar resultado
            resultado = []
            for user_id, nome, funcao in responsaveis:
                resultado.append({
                    'user_id': user_id,
                    'nome': nome or 'Nome não informado',
                    'funcao': funcao or 'Função não informada'
                })
            
            print(f"✅ Responsáveis encontrados para ENEL: {len(resultado)}")
            for resp in resultado:
                print(f"   👤 {resp['nome']} ({resp['funcao']}) - ID: {resp['user_id']}")
            
            if len(resultado) == 0:
                print(f"⚠️ Nenhum responsável encontrado para código: {codigo_ccb}")
                print(f"   💡 Verifique se o código está cadastrado na base CCB")
            
            return resultado
            
        finally:
            conn.close()
            # Limpar cache temporário
            try:
                os.unlink(db_path)
            except:
                pass
        
    except Exception as e:
        print(f"❌ Erro consultando responsáveis ENEL: {e}")
        return []

def obter_administradores_sistema():
    """
    Buscar todos os administradores cadastrados na base CCB Alerta
    
    Returns:
        list: Lista de administradores [{'user_id': int, 'nome': str}]
    """
    try:
        import sqlite3
        import os
        
        print(f"👥 Buscando administradores na base CCB Alerta...")
        
        # Caminho da base CCB Alerta
        db_path = os.path.join(os.getcwd(), 'alertas_bot.db')
        
        if not os.path.exists(db_path):
            print(f"❌ Base CCB Alerta não encontrada: {db_path}")
            return []
        
        # Conectar e buscar administradores
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, nome, data_adicao 
            FROM administradores 
            WHERE user_id IS NOT NULL
            ORDER BY data_adicao DESC
        """)
        
        admins = cursor.fetchall()
        conn.close()
        
        # Formatar resposta
        administradores = []
        for admin in admins:
            administradores.append({
                'user_id': admin[0],
                'nome': admin[1] if admin[1] else f"Admin_{admin[0]}",
                'funcao': 'Administrador',
                'data_adicao': admin[2]
            })
        
        print(f"✅ Encontrados {len(administradores)} administradores na base")
        for admin in administradores:
            print(f"   👤 {admin['nome']} (ID: {admin['user_id']})")
        
        return administradores
        
    except Exception as e:
        print(f"❌ Erro buscando administradores na base: {e}")
        return []

def testar_conexao_enel_ccb():
    """
    Função de teste para verificar conexão ENEL com base CCB
    """
    try:
        print(f"\n🧪 TESTE CONEXÃO ENEL → CCB")
        print(f"=" * 40)
        
        # Verificações básicas (mesmas do BRK)
        onedrive_alerta_id = os.getenv("ONEDRIVE_ALERTA_ID")
        print(f"📁 ONEDRIVE_ALERTA_ID: {'✅ Configurado' if onedrive_alerta_id else '❌ Não configurado'}")
        
        if not onedrive_alerta_id:
            return False
        
        auth_manager = MicrosoftAuth()
        print(f"🔐 Auth Microsoft: {'✅ Disponível' if auth_manager.access_token else '❌ Não disponível'}")
        
        if not auth_manager.access_token:
            return False
        
        # Testar extração de códigos de casas ENEL
        casas_teste = [
            "BR 21-0270 - CENTRO",
            "ADM – MAUA – SP", 
            "BR 21-0271 - JARDIM PRIMAVERA"
        ]
        
        print(f"🎯 Testando extração de códigos:")
        for casa in casas_teste:
            codigo = extrair_codigo_ccb_da_casa_enel(casa)
            print(f"   🏪 {casa[:30]}... → {codigo}")
        
        # Testar acesso ao database (mesma lógica BRK)
        headers = auth_manager.obter_headers_autenticados()
        url = f"https://graph.microsoft.com/v1.0/me/drive/items/{onedrive_alerta_id}/children"
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"☁️ Acesso pasta /Alerta/: {'✅ OK' if response.status_code == 200 else '❌ Falhou'}")
        
        if response.status_code != 200:
            return False
        
        # Verificar se alertas_bot.db existe
        arquivos = response.json().get('value', [])
        db_encontrado = any(arquivo.get('name', '').lower() == 'alertas_bot.db' for arquivo in arquivos)
        
        print(f"💾 alertas_bot.db: {'✅ Encontrado' if db_encontrado else '❌ Não encontrado'}")
        
        if db_encontrado:
            print(f"✅ Teste conexão ENEL → CCB: SUCESSO")
            return True
        else:
            print(f"❌ Teste conexão ENEL → CCB: alertas_bot.db não encontrado")
            return False
        
    except Exception as e:
        print(f"❌ Teste conexão ENEL → CCB: FALHOU - {e}")
        return False

def buscar_responsaveis_por_instalacao(numero_instalacao, relacionamentos_dados):
    """
    Buscar responsáveis por número de instalação ENEL
    
    Fluxo:
    1. Instalação → Buscar casa na planilha relacionamento
    2. Casa → Extrair código CCB
    3. Código CCB → Buscar responsáveis
    
    Args:
        numero_instalacao (str): Número da instalação ENEL
        relacionamentos_dados (list): Dados da planilha relacionamento
        
    Returns:
        list: Lista de responsáveis ou []
    """
    try:
        print(f"🔍 Buscando responsáveis por instalação: {numero_instalacao}")
        
        # 1. Buscar casa pela instalação
        casa_encontrada = None
        for registro in relacionamentos_dados:
            if str(registro.get('Instalacao', '')).strip() == str(numero_instalacao).strip():
                casa_encontrada = registro.get('Casa', '')
                break
        
        if not casa_encontrada:
            print(f"⚠️ Casa não encontrada para instalação: {numero_instalacao}")
            return []
            
        print(f"🏪 Casa encontrada: {casa_encontrada}")
        
        # 2. Buscar responsáveis pela casa
        return obter_responsaveis_por_casa_enel(casa_encontrada)
        
    except Exception as e:
        print(f"❌ Erro buscando responsáveis por instalação: {e}")
        return []