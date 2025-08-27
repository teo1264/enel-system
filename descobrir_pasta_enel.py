#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 DESCOBRIR ID DA PASTA ENEL NO ONEDRIVE
📁 FUNÇÃO: Localizar e mostrar ID da pasta ENEL
👨‍💼 USO: python descobrir_pasta_enel.py
"""

import os
import requests
from auth.microsoft_auth import MicrosoftAuth

def descobrir_pasta_enel():
    """
    Descobrir ID da pasta ENEL no OneDrive
    """
    try:
        print("🔍 DESCOBRINDO PASTA ENEL NO ONEDRIVE")
        print("=" * 50)
        
        # Autenticar
        auth_manager = MicrosoftAuth()
        if not auth_manager.access_token:
            print("❌ Token de acesso não disponível")
            print("💡 Execute primeiro o sistema para autenticar")
            return
        
        headers = auth_manager.obter_headers_autenticados()
        
        # Listar todas as pastas na raiz do OneDrive
        print("📁 Buscando pastas na raiz do OneDrive...")
        url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Erro consultando OneDrive: HTTP {response.status_code}")
            return
        
        pastas = response.json().get('value', [])
        
        print(f"📊 Encontradas {len(pastas)} itens na raiz do OneDrive:")
        print()
        
        pasta_enel_encontrada = False
        
        for item in pastas:
            nome = item.get('name', 'Sem nome')
            item_id = item.get('id', 'Sem ID')
            tipo = 'Pasta' if item.get('folder') else 'Arquivo'
            
            print(f"📂 {nome}")
            print(f"   🔑 ID: {item_id}")
            print(f"   📋 Tipo: {tipo}")
            print()
            
            # Verificar se é pasta relacionada à ENEL
            if any(palavra in nome.upper() for palavra in ['ENEL', 'ENERGIA', 'ELETRIC']):
                print(f"🎯 POSSÍVEL PASTA ENEL ENCONTRADA!")
                print(f"   📁 Nome: {nome}")
                print(f"   🔑 ID: {item_id}")
                print(f"   💡 Use este ID para ONEDRIVE_ENEL_ID")
                print()
                pasta_enel_encontrada = True
        
        if not pasta_enel_encontrada:
            print("⚠️ Nenhuma pasta relacionada à ENEL encontrada na raiz")
            print("💡 Verifique se:")
            print("   - A pasta existe no OneDrive")
            print("   - Tem permissão de acesso")
            print("   - Não está dentro de outra pasta")
        
        print("✅ Busca concluída!")
        
    except Exception as e:
        print(f"❌ Erro descobrindo pasta ENEL: {e}")

if __name__ == "__main__":
    descobrir_pasta_enel()