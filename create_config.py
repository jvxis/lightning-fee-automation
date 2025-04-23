#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Arquivo de configuração padrão para o gerenciador de taxas
"""

import json

# Configuração padrão
DEFAULT_CONFIG = {
    "update_interval_seconds": 3600,  # 1 hora
    "fee_strategy": "balanced",  # balanced, competitive, profitable
    "min_base_fee_msat": 1000,
    "max_base_fee_msat": 5000,
    "min_fee_rate": 0.000001,  # 1 ppm
    "max_fee_rate": 0.001,     # 1000 ppm
    "time_lock_delta": 40,
    "flow_weight": 0.7,        # Peso do fluxo no cálculo
    "peer_weight": 0.3,        # Peso das taxas dos peers no cálculo
    "high_flow_threshold": 0.8, # Percentual de capacidade considerado alto fluxo
    "low_flow_threshold": 0.2,  # Percentual de capacidade considerado baixo fluxo
    "enabled_channels": [],     # Lista vazia significa todos os canais
    "excluded_channels": []     # Canais a serem excluídos da automação
}

# Salvar configuração padrão em um arquivo
with open("fee_config.json", "w") as f:
    json.dump(DEFAULT_CONFIG, f, indent=2, sort_keys=True)

print("Arquivo de configuração padrão criado: fee_config.json")
