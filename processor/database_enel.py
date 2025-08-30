#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 DATABASE ENEL - SQLite Manager
💾 FUNÇÃO: Gerenciar database SQLite para faturas ENEL (baseado no BRK)
🔧 DESCRIÇÃO: Storage no OneDrive + cache local temporário
👨‍💼 AUTOR: Baseado no padrão BRK que funciona no Render
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib
import base64

class DatabaseEnel:
    """
    Gerenciador de Database SQLite ENEL
    
    BASEADO NO PADRÃO BRK QUE FUNCIONA:
    - SQLite como fonte da verdade
    - Storage no OneDrive (permanente)  
    - Cache local temporário (perdido no deploy)
    - 18 campos da planilha ENEL
    """
    
    def __init__(self, onedrive_manager):
        """
        Inicializar database ENEL
        
        Args:
            onedrive_manager: Instância do OneDriveManagerEnel
        """
        self.onedrive = onedrive_manager
        
        # Paths do database
        self.db_local = "/opt/render/project/storage/database_enel.db"  # Cache temporário
        self.db_onedrive_path = "/ENEL/Database/database_enel.db"       # OneDrive permanente
        
        # Criar diretório local
        os.makedirs(os.path.dirname(self.db_local), exist_ok=True)
        
        # Inicializar database
        self._inicializar_database()
        
        print(f"📊 Database ENEL inicializado")
        print(f"   Local (cache): {self.db_local}")
        print(f"   OneDrive: {self.db_onedrive_path}")
    
    def _inicializar_database(self):
        """Criar tabelas se não existirem (baseado no BRK + planilha ENEL)"""
        try:
            # Tentar baixar database existente do OneDrive
            self._baixar_database_onedrive()
            
            conn = sqlite3.connect(self.db_local)
            cursor = conn.cursor()
            
            # Criar tabela faturas_enel (baseada no BRK + 18 campos planilha)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS faturas_enel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    
                    -- Controle processamento (padrão BRK)
                    data_processamento DATETIME NOT NULL,
                    status_duplicata TEXT,
                    observacao TEXT,
                    email_id TEXT NOT NULL,
                    nome_arquivo_original TEXT NOT NULL,
                    nome_arquivo TEXT NOT NULL,
                    hash_arquivo TEXT,
                    dados_extraidos_ok BOOLEAN DEFAULT 0,
                    relacionamento_usado BOOLEAN DEFAULT 0,
                    content_bytes TEXT,  -- PDF em base64 para backup
                    
                    -- Campos básicos ENEL (conforme planilha)
                    casa_oracao TEXT,
                    competencia TEXT,
                    data_emissao TEXT,
                    nota_fiscal TEXT,
                    vencimento TEXT,
                    valor REAL,
                    consumo_kwh INTEGER,
                    numero_instalacao TEXT,
                    
                    -- Análises consumo (conforme planilha)
                    media_6_meses REAL DEFAULT 0.0,
                    diferenca_percentual REAL DEFAULT 0.0,
                    porcentagem_consumo REAL DEFAULT 100.0,
                    alerta_consumo TEXT DEFAULT 'Normal',
                    
                    -- Energia fotovoltaica (conforme planilha)
                    sistema_fotovoltaico TEXT DEFAULT 'Não',
                    compensacao_tusd REAL DEFAULT 0.0,
                    compensacao_te REAL DEFAULT 0.0,
                    total_compensacao REAL DEFAULT 0.0,
                    valor_integral_sem_fv REAL DEFAULT 0.0,
                    percentual_economia_fv REAL DEFAULT 0.0
                )
            ''')
            
            conn.commit()
            conn.close()
            
            print("✅ Database ENEL inicializado com sucesso")
            
        except Exception as e:
            print(f"❌ Erro inicializando database: {e}")
    
    def _baixar_database_onedrive(self):
        """Baixar database do OneDrive se existir"""
        try:
            if self.onedrive:
                # Tentar baixar database existente
                content = self.onedrive.baixar_arquivo("Database", "database_enel.db")
                if content:
                    with open(self.db_local, 'wb') as f:
                        f.write(content)
                    print("✅ Database baixado do OneDrive")
                    return True
            return False
        except Exception as e:
            print(f"⚠️ Database não encontrado no OneDrive (primeira execução): {e}")
            return False
    
    def _fazer_backup_onedrive(self):
        """Fazer backup do database no OneDrive"""
        try:
            if not self.onedrive:
                return False
            
            # Upload do database para OneDrive
            with open(self.db_local, 'rb') as f:
                content = f.read()
            
            sucesso = self.onedrive.salvar_arquivo_binario("Database", "database_enel.db", content)
            
            if sucesso:
                print("✅ Backup database OneDrive realizado")
                return True
            else:
                print("❌ Erro no backup database OneDrive")
                return False
                
        except Exception as e:
            print(f"❌ Erro fazendo backup OneDrive: {e}")
            return False
    
    def inserir_fatura(self, dados_fatura: Dict, email_id: str, pdf_content: bytes = None) -> bool:
        """
        Inserir fatura no database (padrão BRK adaptado para ENEL)
        
        Args:
            dados_fatura: Dados extraídos da fatura
            email_id: ID do email original
            pdf_content: Conteúdo do PDF para backup
            
        Returns:
            bool: True se inserido com sucesso
        """
        try:
            conn = sqlite3.connect(self.db_local)
            cursor = conn.cursor()
            
            # Hash do arquivo para detectar duplicatas
            hash_arquivo = None
            content_b64 = None
            
            if pdf_content:
                hash_arquivo = hashlib.md5(pdf_content).hexdigest()
                content_b64 = base64.b64encode(pdf_content).decode('utf-8')
            
            # Verificar duplicata por hash
            if hash_arquivo:
                cursor.execute('SELECT id FROM faturas_enel WHERE hash_arquivo = ?', (hash_arquivo,))
                if cursor.fetchone():
                    print(f"⚠️ Fatura duplicada detectada (hash: {hash_arquivo[:8]}...)")
                    conn.close()
                    return False
            
            # Inserir fatura
            cursor.execute('''
                INSERT INTO faturas_enel (
                    data_processamento, email_id, nome_arquivo_original, nome_arquivo,
                    hash_arquivo, casa_oracao, competencia, data_emissao, nota_fiscal,
                    vencimento, valor, consumo_kwh, numero_instalacao,
                    sistema_fotovoltaico, compensacao_tusd, compensacao_te, 
                    total_compensacao, valor_integral_sem_fv, percentual_economia_fv,
                    dados_extraidos_ok, content_bytes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                email_id,
                dados_fatura.get('arquivo', 'unknown.pdf'),
                dados_fatura.get('nome_arquivo_renomeado', ''),
                hash_arquivo,
                dados_fatura.get('casa_oracao', ''),
                dados_fatura.get('competencia', ''),
                dados_fatura.get('data_emissao', ''),
                dados_fatura.get('nota_fiscal', ''),
                dados_fatura.get('data_vencimento', ''),
                dados_fatura.get('valor_total_num', 0.0),
                dados_fatura.get('consumo_kwh_num', 0),
                dados_fatura.get('numero_instalacao', ''),
                dados_fatura.get('sistema_fotovoltaico', 'Não'),
                dados_fatura.get('compensacao_tusd_num', 0.0),
                dados_fatura.get('compensacao_te_num', 0.0),
                dados_fatura.get('total_compensacao', 0.0),
                dados_fatura.get('valor_integral_sem_fv', 0.0),
                dados_fatura.get('percentual_economia_fv', 0.0),
                1 if dados_fatura.get('valor_total_num') is not None else 0,
                content_b64
            ))
            
            fatura_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Fazer backup no OneDrive
            self._fazer_backup_onedrive()
            
            print(f"✅ Fatura inserida no database (ID: {fatura_id})")
            return True
            
        except Exception as e:
            print(f"❌ Erro inserindo fatura no database: {e}")
            return False
    
    def obter_estatisticas(self) -> Dict:
        """Obter estatísticas do database"""
        try:
            conn = sqlite3.connect(self.db_local)
            cursor = conn.cursor()
            
            # Estatísticas gerais
            cursor.execute('SELECT COUNT(*) FROM faturas_enel')
            total_faturas = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM faturas_enel WHERE dados_extraidos_ok = 1')
            extraidos_ok = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT competencia) FROM faturas_enel')
            competencias = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT casa_oracao) FROM faturas_enel WHERE casa_oracao != ""')
            casas_oracao = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_faturas": total_faturas,
                "dados_extraidos_ok": extraidos_ok,
                "competencias_diferentes": competencias,
                "casas_oracao": casas_oracao,
                "database_onedrive": True,
                "ultima_atualizacao": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erro obtendo estatísticas: {e}")
            return {"erro": str(e)}
    
    def buscar_por_instalacao(self, numero_instalacao: str) -> List[Dict]:
        """Buscar faturas por número de instalação"""
        try:
            conn = sqlite3.connect(self.db_local)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT competencia, consumo_kwh, valor, sistema_fotovoltaico, 
                       total_compensacao, data_processamento
                FROM faturas_enel 
                WHERE numero_instalacao = ?
                ORDER BY competencia DESC
            ''', (numero_instalacao,))
            
            resultados = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "competencia": r[0],
                    "consumo_kwh": r[1], 
                    "valor": r[2],
                    "sistema_fotovoltaico": r[3],
                    "total_compensacao": r[4],
                    "data_processamento": r[5]
                }
                for r in resultados
            ]
            
        except Exception as e:
            print(f"❌ Erro buscando por instalação: {e}")
            return []