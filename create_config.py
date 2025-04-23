#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de configuração para o LND Fee Automation
"""

import os
import json
import getpass
from pathlib import Path

def get_input_with_default(prompt, default):
    """Solicita entrada do usuário com valor padrão"""
    response = input(f"{prompt} [{default}]: ").strip()
    return response if response else default

def create_config():
    """Cria o arquivo de configuração com informações do LND e estratégias de taxas"""
    print("\n=== Configuração do LND Fee Automation ===\n")
    
    # Configuração de conexão com o LND
    print("\n--- Configuração de Conexão com o LND ---")
    lnd_host = get_input_with_default("Host do LND", "localhost")
    lnd_port = get_input_with_default("Porta REST do LND", "8080")
    
    # Caminhos para certificado e macaroon
    print("\n--- Arquivos de Autenticação ---")
    print("Caminhos para os arquivos de autenticação do LND")
    
    # Sugerir caminhos padrão com base no sistema operacional
    home = str(Path.home())
    
    # Caminhos padrão para diferentes sistemas
    default_paths = {
        "linux": {
            "cert": f"{home}/.lnd/tls.cert",
            "macaroon": f"{home}/.lnd/data/chain/bitcoin/mainnet/admin.macaroon"
        },
        "darwin": {  # macOS
            "cert": f"{home}/Library/Application Support/Lnd/tls.cert",
            "macaroon": f"{home}/Library/Application Support/Lnd/data/chain/bitcoin/mainnet/admin.macaroon"
        },
        "win32": {
            "cert": os.path.join(os.environ.get("APPDATA", ""), "Lnd\\tls.cert"),
            "macaroon": os.path.join(os.environ.get("APPDATA", ""), "Lnd\\data\\chain\\bitcoin\\mainnet\\admin.macaroon")
        }
    }
    
    # Determinar sistema operacional
    if os.name == "posix":
        if os.uname().sysname.lower() == "darwin":
            platform = "darwin"
        else:
            platform = "linux"
    else:
        platform = "win32"
    
    # Obter caminhos padrão para o sistema atual
    default_cert_path = default_paths.get(platform, default_paths["linux"])["cert"]
    default_macaroon_path = default_paths.get(platform, default_paths["linux"])["macaroon"]
    
    # Verificar se os arquivos existem nos caminhos padrão
    if not os.path.exists(default_cert_path):
        print(f"Aviso: Certificado TLS não encontrado no caminho padrão: {default_cert_path}")
        default_cert_path = "caminho/para/seu/tls.cert"
    
    if not os.path.exists(default_macaroon_path):
        # Tentar encontrar em caminhos alternativos comuns
        alt_macaroon_path = f"{home}/.lnd/admin.macaroon"
        if os.path.exists(alt_macaroon_path):
            default_macaroon_path = alt_macaroon_path
        else:
            print(f"Aviso: Macaroon não encontrado no caminho padrão: {default_macaroon_path}")
            default_macaroon_path = "caminho/para/seu/admin.macaroon"
    
    # Solicitar caminhos ao usuário
    cert_path = get_input_with_default("Caminho para o certificado TLS", default_cert_path)
    macaroon_path = get_input_with_default("Caminho para o admin.macaroon", default_macaroon_path)
    
    # Verificar se os arquivos existem
    if not os.path.exists(os.path.expanduser(cert_path)):
        print(f"Aviso: Certificado TLS não encontrado: {cert_path}")
        print("Você precisará corrigir este caminho manualmente no arquivo config.json")
    
    if not os.path.exists(os.path.expanduser(macaroon_path)):
        print(f"Aviso: Macaroon não encontrado: {macaroon_path}")
        print("Você precisará corrigir este caminho manualmente no arquivo config.json")
    
    # Configuração de estratégias de taxas
    print("\n--- Configuração de Estratégias de Taxas ---")
    
    strategies = ["balanced", "competitive", "profitable"]
    print("Estratégias disponíveis:")
    print("  balanced    - Equilibra receita e competitividade")
    print("  competitive - Prioriza competitividade (taxas menores)")
    print("  profitable  - Prioriza receita (taxas maiores)")
    
    strategy = ""
    while strategy not in strategies:
        strategy = get_input_with_default("Estratégia de taxas", "balanced")
        if strategy not in strategies:
            print(f"Estratégia inválida. Escolha entre: {', '.join(strategies)}")
    
    # Intervalo de atualização
    update_interval = int(get_input_with_default("Intervalo de atualização (segundos)", "3600"))
    
    # Limites de taxas
    print("\n--- Limites de Taxas ---")
    min_base_fee = int(get_input_with_default("Taxa base mínima (msat)", "1000"))
    max_base_fee = int(get_input_with_default("Taxa base máxima (msat)", "5000"))
    
    min_fee_rate = float(get_input_with_default("Taxa proporcional mínima (ex: 0.000001 = 1 ppm)", "0.000001"))
    max_fee_rate = float(get_input_with_default("Taxa proporcional máxima (ex: 0.001 = 1000 ppm)", "0.001"))
    
    # Criar configuração
    config = {
        "lnd_host": lnd_host,
        "lnd_port": int(lnd_port),
        "lnd_cert_path": cert_path,
        "lnd_macaroon_path": macaroon_path,
        "fee_strategy": strategy,
        "update_interval_seconds": update_interval,
        "min_base_fee_msat": min_base_fee,
        "max_base_fee_msat": max_base_fee,
        "min_fee_rate": min_fee_rate,
        "max_fee_rate": max_fee_rate,
        "time_lock_delta": 40,
        "flow_weight": 0.7,
        "peer_weight": 0.3,
        "high_flow_threshold": 0.8,
        "low_flow_threshold": 0.2,
        "excluded_channels": [],
        "enabled_channels": []
    }
    
    # Salvar configuração
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2, sort_keys=True)
    
    print("\n✓ Configuração salva em config.json")
    print("\nVocê pode editar este arquivo manualmente para ajustar configurações adicionais.")

if __name__ == "__main__":
    create_config()
