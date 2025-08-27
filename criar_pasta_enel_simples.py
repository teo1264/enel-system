#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CRIAR PASTA ENEL NO ONEDRIVE - Versão Simples
FUNÇÃO: Criar estrutura de pastas ENEL e obter ID
USO: python criar_pasta_enel_simples.py
"""

import os
import requests
from auth.microsoft_auth import MicrosoftAuth

def criar_pasta_enel_onedrive():
    """
    Criar pasta ENEL no OneDrive e retornar ID
    """
    try:
        print("CRIANDO ESTRUTURA ENEL NO ONEDRIVE")
        print("=" * 50)
        
        # Autenticar
        auth_manager = MicrosoftAuth()
        if not auth_manager.access_token:
            print("ERRO: Token de acesso não disponível")
            print("Execute primeiro o sistema para autenticar")
            return
        
        headers = auth_manager.obter_headers_autenticados()
        
        # Criar pasta principal ENEL
        print("Criando pasta principal ENEL...")
        
        pasta_enel_data = {
            "name": "ENEL",
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail"  # Falha se já existir
        }
        
        url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
        response = requests.post(url, headers=headers, json=pasta_enel_data, timeout=30)
        
        if response.status_code == 201:
            pasta_criada = response.json()
            pasta_enel_id = pasta_criada['id']
            pasta_enel_nome = pasta_criada['name']
            
            print("SUCESSO: Pasta ENEL criada com sucesso!")
            print(f"   Nome: {pasta_enel_nome}")
            print(f"   ID: {pasta_enel_id}")
            print()
            
            # Criar subpastas
            subpastas = [
                "01_Emails_Originais",
                "02_PDFs_Processados", 
                "03_Planilhas_Geradas",
                "04_Backups",
                "05_Temporarios"
            ]
            
            print("Criando subpastas...")
            
            for subpasta in subpastas:
                subpasta_data = {
                    "name": subpasta,
                    "folder": {},
                    "@microsoft.graph.conflictBehavior": "replace"
                }
                
                subpasta_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{pasta_enel_id}/children"
                sub_response = requests.post(subpasta_url, headers=headers, json=subpasta_data, timeout=30)
                
                if sub_response.status_code == 201:
                    print(f"   OK: {subpasta}")
                else:
                    print(f"   AVISO: {subpasta} - {sub_response.status_code}")
            
            print()
            print("CONFIGURAÇÃO PARA O RENDER:")
            print(f"ONEDRIVE_ENEL_ID={pasta_enel_id}")
            print()
            print("SUCESSO: Estrutura ENEL criada com sucesso!")
            
            return pasta_enel_id
            
        elif response.status_code == 409:
            print("AVISO: Pasta ENEL já existe!")
            print("Executando busca para obter ID...")
            
            # Buscar pasta existente
            busca_url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
            busca_response = requests.get(busca_url, headers=headers, timeout=30)
            
            if busca_response.status_code == 200:
                pastas = busca_response.json().get('value', [])
                
                for pasta in pastas:
                    if pasta.get('name', '').upper() == 'ENEL':
                        pasta_id = pasta['id']
                        print("ENCONTRADA: Pasta ENEL encontrada!")
                        print(f"   ID: {pasta_id}")
                        print()
                        print("CONFIGURAÇÃO PARA O RENDER:")
                        print(f"ONEDRIVE_ENEL_ID={pasta_id}")
                        return pasta_id
                        
            print("ERRO: Não foi possível encontrar a pasta ENEL existente")
            
        else:
            print(f"ERRO: Erro criando pasta ENEL: HTTP {response.status_code}")
            print(f"   Resposta: {response.text}")
        
    except Exception as e:
        print(f"ERRO: Erro criando pasta ENEL: {e}")

if __name__ == "__main__":
    criar_pasta_enel_onedrive()