#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Testes para o gerenciador de taxas
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Adicionar diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar o módulo a ser testado
from fee_manager import FeeManager

class TestFeeManager(unittest.TestCase):
    """Testes para o gerenciador de taxas"""
    
    def setUp(self):
        """Configuração para cada teste"""
        # Mock do cliente LND
        self.mock_lnd_client = MagicMock()
        
        # Configurar respostas simuladas
        self.mock_lnd_client.get_info.return_value = {
            "identity_pubkey": "test_pubkey",
            "alias": "test_node",
            "num_active_channels": 3
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
        
        self.mock_lnd_client.get_channel_info.return_value = {
            "channel_id": "123456789",
            "node1_policy": {
                "fee_base_msat": "1000",
                "fee_rate_milli_msat": "1",
                "time_lock_delta": 40
            },
            "node2_policy": {
                "fee_base_msat": "1500",
                "fee_rate_milli_msat": "2",
                "time_lock_delta": 40
            }
        }
        
        self.mock_lnd_client.update_channel_policy.return_value = {
            "failed_updates": []
        }
        
        # Criar gerenciador de taxas com o mock
        self.fee_manager = FeeManager(lnd_client=self.mock_lnd_client)
        
        # Configurar para modo de teste
        self.fee_manager.config = {
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
    
    def test_init(self):
        """Testa a inicialização do gerenciador"""
        self.assertIsNotNone(self.fee_manager)
        self.assertEqual(self.fee_manager.running, False)
        self.assertEqual(self.fee_manager.config["fee_strategy"], "balanced")
    
    def test_load_config(self):
        """Testa o carregamento de configuração"""
        # Simular arquivo de configuração
        with patch('builtins.open', unittest.mock.mock_open(read_data='{"fee_strategy": "competitive"}')):
            self.fee_manager.load_config()
            self.assertEqual(self.fee_manager.config["fee_strategy"], "competitive")
    
    def test_save_config(self):
        """Testa o salvamento de configuração"""
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            self.fee_manager.save_config()
            mock_file.assert_called_once()
    
    def test_get_channel_flow_ratio(self):
        """Testa o cálculo da razão de fluxo do canal"""
        channel = {
            "capacity": "1000000",
            "local_balance": "600000",
            "remote_balance": "400000"
        }
        
        ratio = self.fee_manager._get_channel_flow_ratio(channel)
        self.assertEqual(ratio, 0.6)  # 600000 / 1000000 = 0.6
    
    def test_get_peer_fee_info(self):
        """Testa a obtenção de informações de taxas dos peers"""
        chan_id = "123456789"
        peer_info = self.fee_manager._get_peer_fee_info(chan_id)
        
        self.assertIsNotNone(peer_info)
        self.assertEqual(peer_info["base_fee_msat"], 1500)
        self.assertEqual(peer_info["fee_rate"], 0.000002)
    
    def test_calculate_balanced_fees(self):
        """Testa o cálculo de taxas com estratégia balanceada"""
        channel = {
            "chan_id": "123456789",
            "capacity": "1000000",
            "local_balance": "600000",
            "remote_balance": "400000"
        }
        
        peer_info = {
            "base_fee_msat": 1500,
            "fee_rate": 0.000002
        }
        
        fees = self.fee_manager._calculate_balanced_fees(channel, peer_info)
        
        self.assertIsNotNone(fees)
        self.assertIn("base_fee_msat", fees)
        self.assertIn("fee_rate", fees)
        
        # Verificar se as taxas estão dentro dos limites
        self.assertGreaterEqual(fees["base_fee_msat"], self.fee_manager.config["min_base_fee_msat"])
        self.assertLessEqual(fees["base_fee_msat"], self.fee_manager.config["max_base_fee_msat"])
        self.assertGreaterEqual(fees["fee_rate"], self.fee_manager.config["min_fee_rate"])
        self.assertLessEqual(fees["fee_rate"], self.fee_manager.config["max_fee_rate"])
    
    def test_calculate_competitive_fees(self):
        """Testa o cálculo de taxas com estratégia competitiva"""
        channel = {
            "chan_id": "123456789",
            "capacity": "1000000",
            "local_balance": "600000",
            "remote_balance": "400000"
        }
        
        peer_info = {
            "base_fee_msat": 1500,
            "fee_rate": 0.000002
        }
        
        fees = self.fee_manager._calculate_competitive_fees(channel, peer_info)
        
        self.assertIsNotNone(fees)
        self.assertIn("base_fee_msat", fees)
        self.assertIn("fee_rate", fees)
        
        # Verificar se as taxas são menores que as do peer
        self.assertLess(fees["base_fee_msat"], peer_info["base_fee_msat"])
        self.assertLess(fees["fee_rate"], peer_info["fee_rate"])
    
    def test_calculate_profitable_fees(self):
        """Testa o cálculo de taxas com estratégia lucrativa"""
        channel = {
            "chan_id": "123456789",
            "capacity": "1000000",
            "local_balance": "600000",
            "remote_balance": "400000"
        }
        
        peer_info = {
            "base_fee_msat": 1500,
            "fee_rate": 0.000002
        }
        
        fees = self.fee_manager._calculate_profitable_fees(channel, peer_info)
        
        self.assertIsNotNone(fees)
        self.assertIn("base_fee_msat", fees)
        self.assertIn("fee_rate", fees)
        
        # Verificar se as taxas estão dentro dos limites
        self.assertGreaterEqual(fees["base_fee_msat"], self.fee_manager.config["min_base_fee_msat"])
        self.assertLessEqual(fees["base_fee_msat"], self.fee_manager.config["max_base_fee_msat"])
        self.assertGreaterEqual(fees["fee_rate"], self.fee_manager.config["min_fee_rate"])
        self.assertLessEqual(fees["fee_rate"], self.fee_manager.config["max_fee_rate"])
    
    def test_update_channel_fees(self):
        """Testa a atualização de taxas de um canal"""
        channel = {
            "chan_id": "123456789",
            "channel_point": "txid:0",
            "capacity": "1000000",
            "local_balance": "600000",
            "remote_balance": "400000"
        }
        
        result = self.fee_manager._update_channel_fees(channel)
        self.assertTrue(result)
        self.mock_lnd_client.update_channel_policy.assert_called_once()
    
    def test_update_all_channels(self):
        """Testa a atualização de taxas de todos os canais"""
        result = self.fee_manager.update_all_channels()
        self.assertEqual(result["success"], True)
        self.assertEqual(len(result["updated_channels"]), 2)
    
    def test_start_stop(self):
        """Testa o início e parada do gerenciador"""
        # Testar início
        with patch('threading.Thread'):
            self.fee_manager.start()
            self.assertTrue(self.fee_manager.running)
        
        # Testar parada
        self.fee_manager.stop()
        self.assertFalse(self.fee_manager.running)

if __name__ == "__main__":
    unittest.main()
