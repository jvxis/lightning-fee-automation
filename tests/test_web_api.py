#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Testes para a API web da aplicação
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Adicionar diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar o módulo a ser testado
from web.app import app

class TestWebAPI(unittest.TestCase):
    """Testes para a API web da aplicação"""
    
    def setUp(self):
        """Configuração para cada teste"""
        # Configurar o cliente de teste
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Mock do gerenciador de taxas
        self.mock_fee_manager = MagicMock()
        
        # Configurar respostas simuladas
        self.mock_fee_manager.get_status.return_value = {
            "running": True,
            "strategy": "balanced",
            "last_update": "2025-04-23T21:00:00Z",
            "next_update": "2025-04-23T22:00:00Z"
        }
        
        self.mock_fee_manager.get_config.return_value = {
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
        
        self.mock_fee_manager.update_all_channels.return_value = {
            "success": True,
            "updated_channels": ["123456789", "987654321"],
            "failed_channels": []
        }
        
        self.mock_fee_manager.start.return_value = True
        self.mock_fee_manager.stop.return_value = True
        
        # Mock do cliente LND
        self.mock_lnd_client = MagicMock()
        
        self.mock_lnd_client.get_info.return_value = {
            "identity_pubkey": "test_pubkey",
            "alias": "test_node",
            "num_active_channels": 3,
            "num_pending_channels": 1,
            "num_peers": 5,
            "block_height": 800000,
            "version": "0.15.5-beta"
        }
        
        self.mock_lnd_client.list_channels.return_value = {
            "channels": [
                {
                    "chan_id": "123456789",
                    "channel_point": "txid:0",
                    "capacity": "1000000",
                    "local_balance": "600000",
                    "remote_balance": "400000",
                    "remote_pubkey": "peer1",
                    "active": True
                },
                {
                    "chan_id": "987654321",
                    "channel_point": "txid:1",
                    "capacity": "2000000",
                    "local_balance": "800000",
                    "remote_balance": "1200000",
                    "remote_pubkey": "peer2",
                    "active": True
                }
            ]
        }
        
        # Injetar mocks na aplicação
        app.fee_manager = self.mock_fee_manager
        app.lnd_client = self.mock_lnd_client
    
    def test_index_route(self):
        """Testa a rota principal"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_route(self):
        """Testa a rota do dashboard"""
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
    
    def test_channels_route(self):
        """Testa a rota de canais"""
        response = self.client.get('/channels')
        self.assertEqual(response.status_code, 200)
    
    def test_settings_route(self):
        """Testa a rota de configurações"""
        response = self.client.get('/settings')
        self.assertEqual(response.status_code, 200)
    
    def test_api_node_info(self):
        """Testa a API de informações do node"""
        response = self.client.get('/api/node/info')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["identity_pubkey"], "test_pubkey")
        self.assertEqual(data["alias"], "test_node")
    
    def test_api_channels(self):
        """Testa a API de canais"""
        response = self.client.get('/api/channels')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data["channels"]), 2)
        self.assertEqual(data["channels"][0]["chan_id"], "123456789")
    
    def test_api_fees_status(self):
        """Testa a API de status do gerenciador de taxas"""
        response = self.client.get('/api/fees/status')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["running"], True)
        self.assertEqual(data["strategy"], "balanced")
    
    def test_api_config(self):
        """Testa a API de configuração"""
        # Teste GET
        response = self.client.get('/api/config')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["fee_strategy"], "balanced")
        
        # Teste POST
        new_config = {
            "fee_strategy": "competitive",
            "update_interval_seconds": 1800
        }
        
        self.mock_fee_manager.update_config.return_value = {
            "success": True,
            "config": new_config
        }
        
        response = self.client.post('/api/config', json=new_config)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["success"], True)
    
    def test_api_fees_update(self):
        """Testa a API de atualização de taxas"""
        response = self.client.post('/api/fees/update')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["success"], True)
        self.assertEqual(len(data["updated_channels"]), 2)
    
    def test_api_fees_start(self):
        """Testa a API de início da automação"""
        response = self.client.post('/api/fees/start')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["success"], True)
    
    def test_api_fees_stop(self):
        """Testa a API de parada da automação"""
        response = self.client.post('/api/fees/stop')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["success"], True)
    
    def test_api_channel_fees(self):
        """Testa a API de atualização de taxas de um canal específico"""
        chan_id = "123456789"
        new_fees = {
            "base_fee_msat": 2000,
            "fee_rate": 0.000003,
            "time_lock_delta": 40
        }
        
        self.mock_fee_manager.update_channel_fees.return_value = {
            "success": True,
            "channel_id": chan_id
        }
        
        response = self.client.post(f'/api/channel/{chan_id}/fees', json=new_fees)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["success"], True)
        self.assertEqual(data["channel_id"], chan_id)

if __name__ == "__main__":
    unittest.main()
