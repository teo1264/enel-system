#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📱 TELEGRAM SENDER - VERSÃO COM ANEXO PDF
📧 FUNÇÃO: Enviar mensagens + PDF via Telegram Bot
👨‍💼 RESPONSÁVEL: Sidney Gubitoso - Auxiliar Tesouraria Administrativa Mauá
🆕 FUNCIONALIDADE: Adicionar envio de documentos PDF anexados
"""

import os
import requests
import time
import io
import sqlite3

def enviar_telegram(user_id, mensagem):
    """
    Enviar mensagem via Telegram
    Reutiliza TELEGRAM_BOT_TOKEN do CCB Alerta Bot
    
    Args:
        user_id (str/int): ID do usuário Telegram
        mensagem (str): Mensagem formatada para envio
    
    Returns:
        bool: True se envio bem-sucedido, False caso contrário
    """
    try:
        print(f"📱 Enviando Telegram para user_id: {user_id}")
        
        # 1. Verificar token
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not bot_token:
            print(f"❌ TELEGRAM_BOT_TOKEN não configurado")
            return False
        
        print(f"🤖 Bot token: {bot_token[:20]}...")
        
        # 2. Preparar dados para API
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        data = {
            'chat_id': user_id,
            'text': mensagem,
            'parse_mode': 'Markdown'
        }
        
        print(f"📤 Enviando mensagem ({len(mensagem)} caracteres)...")
        
        # 3. Fazer requisição
        response = requests.post(url, data=data, timeout=10)
        
        # 4. Verificar resultado
        if response.status_code == 200:
            response_data = response.json()
            
            if response_data.get('ok'):
                message_id = response_data.get('result', {}).get('message_id')
                print(f"✅ Telegram enviado com sucesso - Message ID: {message_id}")
                return True
            else:
                error_description = response_data.get('description', 'Erro desconhecido')
                print(f"❌ Telegram API erro: {error_description}")
                return False
        else:
            print(f"❌ Telegram HTTP erro: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Detalhes: {error_data}")
            except:
                print(f"   Resposta: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Timeout enviando Telegram para {user_id}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de rede enviando Telegram: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado enviando Telegram: {e}")
        return False

def enviar_telegram_com_anexo(user_id, mensagem, pdf_bytes, nome_arquivo):
    """
    🆕 FUNÇÃO: Enviar mensagem + PDF anexado via Telegram
    
    Usa API sendDocument do Telegram para enviar PDF como anexo
    
    Args:
        user_id (str/int): ID do usuário Telegram
        mensagem (str): Mensagem formatada (será caption do documento)
        pdf_bytes (bytes): Conteúdo do PDF
        nome_arquivo (str): Nome do arquivo PDF
    
    Returns:
        bool: True se envio bem-sucedido, False caso contrário
    """
    try:
        print(f"📎 Enviando Telegram COM ANEXO para user_id: {user_id}")
        
        # 1. Verificar token
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not bot_token:
            print(f"❌ TELEGRAM_BOT_TOKEN não configurado")
            return False
        
        print(f"🤖 Bot token: {bot_token[:20]}...")
        
        # 2. Verificar limites do Telegram
        if len(pdf_bytes) > 50 * 1024 * 1024:  # 50MB limite Telegram
            print(f"❌ PDF muito grande: {len(pdf_bytes)} bytes (limite: 50MB)")
            return False
        
        print(f"📄 PDF: {len(pdf_bytes)} bytes - {nome_arquivo}")
        
        # 3. Preparar dados para API sendDocument
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        
        # Criar arquivo em memória
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.name = nome_arquivo
        
        # Dados do formulário
        data = {
            'chat_id': user_id,
            'caption': mensagem,
            'parse_mode': 'Markdown'
        }
        
        # Arquivo para upload
        files = {
            'document': (nome_arquivo, pdf_file, 'application/pdf')
        }
        
        print(f"📤 Enviando documento via sendDocument...")
        
        # 4. Fazer requisição (timeout maior para upload)
        response = requests.post(url, data=data, files=files, timeout=180)
        
        # 5. Verificar resultado
        if response.status_code == 200:
            response_data = response.json()
            
            if response_data.get('ok'):
                message_id = response_data.get('result', {}).get('message_id')
                print(f"✅ Telegram com anexo enviado - Message ID: {message_id}")
                return True
            else:
                error_description = response_data.get('description', 'Erro desconhecido')
                print(f"❌ Telegram API erro: {error_description}")
                return False
        else:
            print(f"❌ Telegram HTTP erro: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Detalhes: {error_data}")
            except:
                print(f"   Resposta: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Timeout enviando Telegram com anexo para {user_id}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de rede enviando Telegram com anexo: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado enviando Telegram com anexo: {e}")
        return False
    finally:
        # Limpar arquivo da memória
        try:
            if 'pdf_file' in locals():
                pdf_file.close()
        except:
            pass

def enviar_telegram_bulk(user_ids, mensagem, delay_segundos=1):
    """
    Enviar mensagem para múltiplos usuários com delay
    Evita rate limiting do Telegram
    
    Args:
        user_ids (list): Lista de IDs dos usuários
        mensagem (str): Mensagem para envio
        delay_segundos (int): Delay entre envios (padrão: 1 segundo)
    
    Returns:
        dict: Resultado detalhado dos envios
    """
    try:
        print(f"📱 Enviando Telegram em lote para {len(user_ids)} usuários")
        
        sucessos = 0
        falhas = 0
        detalhes = []
        
        for i, user_id in enumerate(user_ids, 1):
            print(f"📤 Enviando {i}/{len(user_ids)} para user_id: {user_id}")
            
            sucesso = enviar_telegram(user_id, mensagem)
            
            if sucesso:
                sucessos += 1
                detalhes.append({'user_id': user_id, 'status': 'sucesso'})
                print(f"✅ {i}/{len(user_ids)}: Sucesso")
            else:
                falhas += 1
                detalhes.append({'user_id': user_id, 'status': 'falha'})
                print(f"❌ {i}/{len(user_ids)}: Falha")
            
            # Delay entre envios (exceto no último)
            if i < len(user_ids) and delay_segundos > 0:
                print(f"⏱️ Aguardando {delay_segundos}s...")
                time.sleep(delay_segundos)
        
        resultado = {
            'total_usuarios': len(user_ids),
            'sucessos': sucessos,
            'falhas': falhas,
            'taxa_sucesso': (sucessos / len(user_ids)) * 100 if user_ids else 0,
            'detalhes': detalhes
        }
        
        print(f"📊 RESULTADO BULK TELEGRAM:")
        print(f"   👥 Total usuários: {resultado['total_usuarios']}")
        print(f"   ✅ Sucessos: {resultado['sucessos']}")
        print(f"   ❌ Falhas: {resultado['falhas']}")
        print(f"   📈 Taxa sucesso: {resultado['taxa_sucesso']:.1f}%")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro no envio bulk: {e}")
        return {
            'total_usuarios': len(user_ids) if user_ids else 0,
            'sucessos': 0,
            'falhas': len(user_ids) if user_ids else 0,
            'taxa_sucesso': 0,
            'erro': str(e)
        }

def enviar_telegram_bulk_com_anexo(user_ids, mensagem, pdf_bytes, nome_arquivo, delay_segundos=2):
    """
    🆕 FUNÇÃO: Enviar mensagem + PDF para múltiplos usuários
    
    Args:
        user_ids (list): Lista de IDs dos usuários
        mensagem (str): Mensagem para envio
        pdf_bytes (bytes): Conteúdo do PDF
        nome_arquivo (str): Nome do arquivo PDF
        delay_segundos (int): Delay entre envios (padrão: 2 segundos para documentos)
    
    Returns:
        dict: Resultado detalhado dos envios
    """
    try:
        print(f"📎 Enviando Telegram com anexo em lote para {len(user_ids)} usuários")
        
        sucessos = 0
        falhas = 0
        detalhes = []
        
        for i, user_id in enumerate(user_ids, 1):
            print(f"📤 Enviando {i}/{len(user_ids)} para user_id: {user_id}")
            
            sucesso = enviar_telegram_com_anexo(user_id, mensagem, pdf_bytes, nome_arquivo)
            
            if sucesso:
                sucessos += 1
                detalhes.append({'user_id': user_id, 'status': 'sucesso'})
                print(f"✅ {i}/{len(user_ids)}: Sucesso")
            else:
                falhas += 1
                detalhes.append({'user_id': user_id, 'status': 'falha'})
                print(f"❌ {i}/{len(user_ids)}: Falha")
            
            # Delay entre envios (mais longo para documentos)
            if i < len(user_ids) and delay_segundos > 0:
                print(f"⏱️ Aguardando {delay_segundos}s...")
                time.sleep(delay_segundos)
        
        resultado = {
            'total_usuarios': len(user_ids),
            'sucessos': sucessos,
            'falhas': falhas,
            'taxa_sucesso': (sucessos / len(user_ids)) * 100 if user_ids else 0,
            'detalhes': detalhes
        }
        
        print(f"📊 RESULTADO BULK TELEGRAM COM ANEXO:")
        print(f"   👥 Total usuários: {resultado['total_usuarios']}")
        print(f"   ✅ Sucessos: {resultado['sucessos']}")
        print(f"   ❌ Falhas: {resultado['falhas']}")
        print(f"   📈 Taxa sucesso: {resultado['taxa_sucesso']:.1f}%")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro no envio bulk com anexo: {e}")
        return {
            'total_usuarios': len(user_ids) if user_ids else 0,
            'sucessos': 0,
            'falhas': len(user_ids) if user_ids else 0,
            'taxa_sucesso': 0,
            'erro': str(e)
        }

def _obter_administradores_da_base():
    """
    Obter IDs dos administradores da base CCB Alerta
    
    Returns:
        str: IDs dos administradores separados por vírgula
    """
    try:
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

def testar_telegram_bot():
    """
    Testar funcionamento do bot Telegram
    Envia mensagem de teste para admin
    """
    try:
        print(f"\n🧪 TESTE TELEGRAM BOT")
        print(f"="*30)
        
        # Verificar configurações
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        admin_ids_str = _obter_administradores_da_base()
        admin_ids = admin_ids_str.split(",") if admin_ids_str else []
        
        print(f"🤖 Bot token: {'✅ Configurado' if bot_token else '❌ Não configurado'}")
        print(f"👨‍💼 Admin IDs (base): {'✅ Encontrados' if admin_ids and admin_ids[0] else '❌ Nenhum admin na base'}")
        
        if not bot_token:
            print(f"❌ Configure TELEGRAM_BOT_TOKEN")
            return False
        
        if not admin_ids or not admin_ids[0].strip():
            print(f"❌ Nenhum administrador encontrado na base CCB Alerta")
            return False
        
        # Testar info do bot
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_data = bot_info.get('result', {})
                print(f"🤖 Bot ativo: @{bot_data.get('username', 'N/A')}")
                print(f"🏷️ Nome: {bot_data.get('first_name', 'N/A')}")
            else:
                print(f"❌ Bot token inválido")
                return False
        else:
            print(f"❌ Erro consultando bot: HTTP {response.status_code}")
            return False
        
        # Enviar mensagem de teste para admin
        admin_id = admin_ids[0].strip()
        mensagem_teste = """🧪 *TESTE SISTEMA BRK + CCB ALERTA*

✅ Bot Telegram funcionando  
✅ Integração Sistema BRK ativa  
✅ Base CCB Alerta conectada  
✅ Envio de anexos PDF ativo  

🤖 *Sistema BRK Automático*
🔧 *Teste realizado com sucesso!*"""
        
        print(f"📤 Enviando mensagem teste para admin: {admin_id}")
        sucesso = enviar_telegram(admin_id, mensagem_teste)
        
        if sucesso:
            print(f"✅ Teste Telegram Bot: SUCESSO")
            return True
        else:
            print(f"❌ Teste Telegram Bot: FALHOU")
            return False
        
    except Exception as e:
        print(f"❌ Erro teste Telegram Bot: {e}")
        return False

def testar_telegram_com_anexo():
    """
    🆕 FUNÇÃO: Testar envio de documento PDF
    Envia PDF de teste para admin
    """
    try:
        print(f"\n🧪 TESTE TELEGRAM COM ANEXO")
        print(f"="*35)
        
        # Verificar configurações
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        admin_ids_str = _obter_administradores_da_base()
        admin_ids = admin_ids_str.split(",") if admin_ids_str else []
        
        if not bot_token or not admin_ids or not admin_ids[0].strip():
            print(f"❌ Configurações não disponíveis")
            return False
        
        admin_id = admin_ids[0].strip()
        
        # Criar PDF de teste simples
        pdf_teste = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(TESTE PDF BRK) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n299\n%%EOF'
        
        mensagem_teste = """🧪 *TESTE ANEXO PDF - SISTEMA BRK*

✅ Funcionalidade anexo ativa  
📎 PDF de teste anexado  
🤖 Sistema BRK + CCB Alerta  

🔧 *Teste realizado com sucesso!*"""
        
        print(f"📤 Enviando PDF teste para admin: {admin_id}")
        sucesso = enviar_telegram_com_anexo(admin_id, mensagem_teste, pdf_teste, "teste-brk.pdf")
        
        if sucesso:
            print(f"✅ Teste anexo PDF: SUCESSO")
            return True
        else:
            print(f"❌ Teste anexo PDF: FALHOU")
            return False
        
    except Exception as e:
        print(f"❌ Erro teste anexo PDF: {e}")
        return False

def verificar_configuracao_telegram():
    """
    Verificar se configurações Telegram estão corretas
    Útil para debug sem enviar mensagens
    """
    try:
        print(f"\n🔍 VERIFICAÇÃO CONFIGURAÇÃO TELEGRAM")
        print(f"="*40)
        
        admin_ids_str = _obter_administradores_da_base()
        admin_ids_da_base = admin_ids_str.split(",") if admin_ids_str else []
        
        configuracao = {
            'bot_token_configurado': bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            'admin_ids_configurado': bool(admin_ids_da_base),
            'bot_token_valido': False,
            'admin_ids_validos': [],
            'suporte_anexos': True  # ✅ Funcionalidade anexos disponível
        }
        
        # Verificar bot token
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if bot_token:
            try:
                url = f"https://api.telegram.org/bot{bot_token}/getMe"
                response = requests.get(url, timeout=5)
                if response.status_code == 200 and response.json().get('ok'):
                    configuracao['bot_token_valido'] = True
            except:
                pass
        
        # Verificar admin IDs
        for admin_id in admin_ids_da_base:
            admin_id = admin_id.strip()
            if admin_id and admin_id.isdigit():
                configuracao['admin_ids_validos'].append(admin_id)
        
        print(f"🤖 Bot token: {'✅ Válido' if configuracao['bot_token_valido'] else '❌ Inválido'}")
        print(f"👨‍💼 Admin IDs (base): {len(configuracao['admin_ids_validos'])} válido(s)")
        print(f"📎 Suporte anexos: {'✅ Disponível' if configuracao['suporte_anexos'] else '❌ Indisponível'}")
        
        for admin_id in configuracao['admin_ids_validos']:
            print(f"   👤 {admin_id}")
        
        tudo_ok = (configuracao['bot_token_valido'] and 
                  len(configuracao['admin_ids_validos']) > 0 and
                  configuracao['suporte_anexos'])
        
        print(f"📊 Configuração geral: {'✅ OK' if tudo_ok else '❌ Problemas detectados'}")
        
        return configuracao
        
    except Exception as e:
        print(f"❌ Erro verificando configuração: {e}")
        return {'erro': str(e)}
