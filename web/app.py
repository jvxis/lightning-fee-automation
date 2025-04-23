#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aplicação web para gerenciamento de taxas do LND
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for

# Adicionar diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar os módulos do projeto
from lnd_client_rest import LNDClient
from fee_manager import FeeManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("web_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("web_app")

# Inicializar a aplicação Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Variáveis globais
lnd_client = None
fee_manager = None
dev_mode = os.environ.get("LND_DEV_MODE", "0") == "1"

def initialize_app():
    """Inicializa o cliente LND e o gerenciador de taxas"""
    global lnd_client, fee_manager
    
    try:
        # Criar cliente LND
        lnd_client = LNDClient()
        
        # Criar gerenciador de taxas
        fee_manager = FeeManager(lnd_client)
        
        logger.info("Aplicação inicializada com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar aplicação: {e}")
        return False

@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html', dev_mode=dev_mode)

@app.route('/dashboard')
def dashboard():
    """Dashboard principal"""
    return render_template('dashboard.html', dev_mode=dev_mode)

@app.route('/channels')
def channels():
    """Página de gerenciamento de canais"""
    return render_template('channels.html', dev_mode=dev_mode)

@app.route('/settings')
def settings():
    """Página de configurações"""
    return render_template('settings.html', dev_mode=dev_mode)

@app.route('/api/node/info')
def api_node_info():
    """API para obter informações do node"""
    try:
        info = lnd_client.get_info()
        return jsonify(info)
    except Exception as e:
        logger.error(f"Erro ao obter informações do node: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/channels')
def api_channels():
    """API para listar canais"""
    try:
        channels = lnd_client.list_channels()
        return jsonify(channels)
    except Exception as e:
        logger.error(f"Erro ao listar canais: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/channel/<chan_id>')
def api_channel_info(chan_id):
    """API para obter informações de um canal específico"""
    try:
        channel_info = lnd_client.get_channel_info(chan_id)
        
        # Adicionar estatísticas do canal se disponíveis
        if fee_manager and chan_id in fee_manager.channel_stats:
            channel_info["stats"] = fee_manager.channel_stats[chan_id]
        
        return jsonify(channel_info)
    except Exception as e:
        logger.error(f"Erro ao obter informações do canal {chan_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/config', methods=['GET'])
def api_get_config():
    """API para obter configuração atual"""
    try:
        if fee_manager:
            return jsonify(fee_manager.config)
        else:
            return jsonify({"error": "Gerenciador de taxas não inicializado"}), 500
    except Exception as e:
        logger.error(f"Erro ao obter configuração: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/config', methods=['POST'])
def api_update_config():
    """API para atualizar configuração"""
    try:
        if not fee_manager:
            return jsonify({"error": "Gerenciador de taxas não inicializado"}), 500
        
        # Obter nova configuração do corpo da requisição
        new_config = request.json
        
        # Atualizar configuração
        for key, value in new_config.items():
            if key in fee_manager.config:
                fee_manager.config[key] = value
        
        # Salvar configuração
        fee_manager.save_config()
        
        return jsonify({"success": True, "config": fee_manager.config})
    except Exception as e:
        logger.error(f"Erro ao atualizar configuração: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fees/update', methods=['POST'])
def api_update_fees():
    """API para atualizar taxas manualmente"""
    try:
        if not fee_manager:
            return jsonify({"error": "Gerenciador de taxas não inicializado"}), 500
        
        # Executar atualização de taxas
        fee_manager.run_once()
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Erro ao atualizar taxas: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fees/start', methods=['POST'])
def api_start_fee_manager():
    """API para iniciar o gerenciador de taxas"""
    try:
        if not fee_manager:
            return jsonify({"error": "Gerenciador de taxas não inicializado"}), 500
        
        # Iniciar gerenciador de taxas
        fee_manager.start()
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Erro ao iniciar gerenciador de taxas: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fees/stop', methods=['POST'])
def api_stop_fee_manager():
    """API para parar o gerenciador de taxas"""
    try:
        if not fee_manager:
            return jsonify({"error": "Gerenciador de taxas não inicializado"}), 500
        
        # Parar gerenciador de taxas
        fee_manager.stop()
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Erro ao parar gerenciador de taxas: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fees/status')
def api_fee_manager_status():
    """API para verificar o status do gerenciador de taxas"""
    try:
        if not fee_manager:
            return jsonify({"error": "Gerenciador de taxas não inicializado"}), 500
        
        return jsonify({
            "running": fee_manager.running,
            "update_interval": fee_manager.config["update_interval_seconds"],
            "strategy": fee_manager.config["fee_strategy"]
        })
    except Exception as e:
        logger.error(f"Erro ao verificar status do gerenciador de taxas: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/channel/<chan_id>/fees', methods=['POST'])
def api_update_channel_fees(chan_id):
    """API para atualizar taxas de um canal específico"""
    try:
        if not lnd_client:
            return jsonify({"error": "Cliente LND não inicializado"}), 500
        
        # Obter parâmetros da requisição
        data = request.json
        base_fee_msat = data.get("base_fee_msat")
        fee_rate = data.get("fee_rate")
        time_lock_delta = data.get("time_lock_delta")
        
        # Obter informações do canal para construir o chan_point
        channels = lnd_client.list_channels()
        channel = None
        
        for ch in channels.get("channels", []):
            if ch["chan_id"] == chan_id:
                channel = ch
                break
        
        if not channel:
            return jsonify({"error": f"Canal {chan_id} não encontrado"}), 404
        
        # Preparar ponto do canal
        funding_txid = channel["channel_point"].split(":")[0]
        output_index = int(channel["channel_point"].split(":")[1])
        chan_point = {
            "funding_txid_str": funding_txid,
            "output_index": output_index
        }
        
        # Atualizar taxas do canal
        result = lnd_client.update_channel_policy(
            global_update=False,
            chan_point=chan_point,
            base_fee_msat=base_fee_msat,
            fee_rate=fee_rate,
            time_lock_delta=time_lock_delta
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Erro ao atualizar taxas do canal {chan_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/dev/mode', methods=['POST'])
def api_set_dev_mode():
    """API para ativar/desativar modo de desenvolvimento"""
    try:
        global dev_mode
        
        # Obter novo estado do modo de desenvolvimento
        data = request.json
        new_dev_mode = data.get("dev_mode", False)
        
        # Atualizar variável de ambiente
        os.environ["LND_DEV_MODE"] = "1" if new_dev_mode else "0"
        dev_mode = new_dev_mode
        
        return jsonify({"success": True, "dev_mode": dev_mode})
    except Exception as e:
        logger.error(f"Erro ao atualizar modo de desenvolvimento: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Inicializar aplicação
    if initialize_app():
        # Executar aplicação Flask
        app.run(host="0.0.0.0", port=5000, debug=True)
    else:
        logger.error("Falha ao inicializar aplicação")
