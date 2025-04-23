#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de instalação para o LND Fee Automation
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    if sys.version_info < (3, 8):
        print("Erro: Python 3.8 ou superior é necessário.")
        sys.exit(1)
    print("✓ Versão do Python compatível")

def check_pip():
    """Verifica se o pip está instalado"""
    try:
        subprocess.run([sys.executable, "-m", "pip3", "--version"], 
                      check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✓ Pip está instalado")
        return True
    except subprocess.CalledProcessError:
        print("Erro: Pip não está instalado.")
        return False

def install_dependencies():
    """Instala as dependências necessárias"""
    print("\nInstalando dependências...")
    try:
        subprocess.run([sys.executable, "-m", "pip3", "install", "-r", "requirements.txt"], 
                      check=True)
        print("✓ Dependências instaladas com sucesso")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao instalar dependências: {e}")
        return False

def create_default_config():
    """Cria um arquivo de configuração padrão se não existir"""
    config_path = Path("config.json")
    
    if config_path.exists():
        print("✓ Arquivo de configuração já existe")
        return
    
    default_config = {
        "lnd_host": "localhost",
        "lnd_port": 8080,
        "lnd_cert_path": "~/.lnd/tls.cert",
        "lnd_macaroon_path": "~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon",
        "fee_strategy": "balanced",
        "update_interval_seconds": 3600,
        "min_base_fee_msat": 1000,
        "max_base_fee_msat": 5000,
        "min_fee_rate": 0.000001,
        "max_fee_rate": 0.001,
        "time_lock_delta": 40,
        "flow_weight": 0.7,
        "peer_weight": 0.3,
        "high_flow_threshold": 0.8,
        "low_flow_threshold": 0.2,
        "excluded_channels": [],
        "enabled_channels": []
    }
    
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print("✓ Arquivo de configuração padrão criado")

def setup_database():
    """Configura o banco de dados para histórico de taxas"""
    db_path = Path("data")
    if not db_path.exists():
        db_path.mkdir()
        print("✓ Diretório de dados criado")
    
    # Criar arquivo de banco de dados SQLite vazio
    try:
        import sqlite3
        conn = sqlite3.connect('data/fee_history.db')
        cursor = conn.cursor()
        
        # Criar tabela para histórico de taxas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fee_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            channel_id TEXT,
            old_base_fee INTEGER,
            new_base_fee INTEGER,
            old_fee_rate REAL,
            new_fee_rate REAL,
            strategy TEXT
        )
        ''')
        
        # Criar tabela para estatísticas de canais
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS channel_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            channel_id TEXT,
            local_balance INTEGER,
            remote_balance INTEGER,
            capacity INTEGER,
            num_updates INTEGER
        )
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Banco de dados inicializado")
    except Exception as e:
        print(f"Erro ao configurar banco de dados: {e}")

def run_config_wizard():
    """Executa o assistente de configuração"""
    print("\nDeseja executar o assistente de configuração? (s/n)")
    choice = input("> ").strip().lower()
    
    if choice == 's':
        try:
            subprocess.run([sys.executable, "create_config.py"], check=True)
            print("✓ Configuração concluída com sucesso")
        except subprocess.CalledProcessError as e:
            print(f"Erro durante a configuração: {e}")
    else:
        print("Assistente de configuração ignorado. Você pode executá-lo mais tarde com 'python create_config.py'")

def create_requirements_file():
    """Cria o arquivo requirements.txt se não existir"""
    req_path = Path("requirements.txt")
    
    if req_path.exists():
        print("✓ Arquivo requirements.txt já existe")
        return
    
    requirements = [
        "flask==2.2.3",
        "requests==2.28.2",
        "pyOpenSSL==23.0.0",
        "cryptography==39.0.1",
        "schedule==1.1.0",
        "python-dateutil==2.8.2",
        "werkzeug==2.2.3",
        "jinja2==3.1.2",
        "itsdangerous==2.1.2",
        "click==8.1.3",
        "markupsafe==2.1.2"
    ]
    
    with open(req_path, 'w') as f:
        f.write("\n".join(requirements))
    
    print("✓ Arquivo requirements.txt criado")

def main():
    """Função principal de instalação"""
    print("=== Instalação do LND Fee Automation ===\n")
    
    # Verificar requisitos
    check_python_version()
    has_pip = check_pip()
    
    if not has_pip:
        print("Por favor, instale o pip e tente novamente.")
        sys.exit(1)
    
    # Criar arquivo requirements.txt
    create_requirements_file()
    
    # Instalar dependências
    if not install_dependencies():
        print("Falha ao instalar dependências. Por favor, verifique os erros e tente novamente.")
        sys.exit(1)
    
    # Criar configuração padrão
    create_default_config()
    
    # Configurar banco de dados
    setup_database()
    
    # Executar assistente de configuração
    run_config_wizard()
    
    print("\n=== Instalação concluída com sucesso! ===")
    print("\nPara iniciar a aplicação, execute:")
    print("  cd web")
    print("  python app.py")
    print("\nA interface web estará disponível em: http://localhost:5000")

if __name__ == "__main__":
    main()
