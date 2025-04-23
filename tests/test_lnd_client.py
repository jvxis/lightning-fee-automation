#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Testes para o cliente LND
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Adicionar diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar o módulo a ser testado
from lnd_client_rest import LNDClient

class TestLNDClient(unittest.TestCase):
    """Testes para o cliente LND"""
    
    def setUp(self):
        """Configuração para cada teste"""
        # Ativar modo de desenvolvimento para simular respostas
        os.environ["LND_DEV_MODE"] = "1"
        self.client = LNDClient()
    
    def test_init(self):
        """Testa a inicialização do cliente"""
        self.assertIsNotNone(self.client)
        self.assertEqual(self.client.lnd_host, "localhost")
        self.assertEqual(self.client.lnd_port, 8080)
        self.assertTrue(self.client.use_rest)
    
    def test_get_info(self):
        """Testa a obtenção de informações do node"""
        info = self.client.get_info()
        self.assertIsNotNone(info)
        self.assertIn("identity_pubkey", info)
        self.assertIn("alias", info)
        self.assertIn("num_active_channels", info)
    
    def test_list_channels(self):
        """Testa a listagem de canais"""
        channels = self.client.list_channels()
        self.assertIsNotNone(channels)
        self.assertIn("channels", channels)
        self.assertIsInstance(channels["channels"], list)
        
        # Verificar se há pelo menos um canal
        if channels["channels"]:
            channel = channels["channels"][0]
            self.assertIn("chan_id", channel)
            self.assertIn("capacity", channel)
            self.assertIn("local_balance", channel)
            self.assertIn("remote_balance", channel)
    
    def test_get_channel_info(self):
        """Testa a obtenção de informações de um canal específico"""
        # Primeiro, obter um ID de canal válido
        channels = self.client.list_channels()
        if not channels["channels"]:
            self.skipTest("Não há canais para testar")
        
        chan_id = channels["channels"][0]["chan_id"]
        chan_info = self.client.get_channel_info(chan_id)
        
        self.assertIsNotNone(chan_info)
        self.assertIn("channel_id", chan_info)
        self.assertIn("node1_policy", chan_info)
        self.assertIn("node2_policy", chan_info)
    
    def test_update_channel_policy(self):
        """Testa a atualização de política de taxas"""
        # Testar atualização global
        result = self.client.update_channel_policy(
            global_update=True,
            base_fee_msat=1000,
            fee_rate=0.000001,
            time_lock_delta=40
        )
        
        self.assertIsNotNone(result)
        self.assertIn("failed_updates", result)
        self.assertEqual(len(result["failed_updates"]), 0)
        
        # Testar atualização de canal específico
        channels = self.client.list_channels()
        if not channels["channels"]:
            self.skipTest("Não há canais para testar")
        
        channel = channels["channels"][0]
        funding_txid = channel["channel_point"].split(":")[0]
        output_index = int(channel["channel_point"].split(":")[1])
        
        chan_point = {
            "funding_txid_str": funding_txid,
            "output_index": output_index
        }
        
        result = self.client.update_channel_policy(
            global_update=False,
            chan_point=chan_point,
            base_fee_msat=1500,
            fee_rate=0.000002,
            time_lock_delta=40
        )
        
        self.assertIsNotNone(result)
        self.assertIn("failed_updates", result)
        self.assertEqual(len(result["failed_updates"]), 0)
    
    def test_error_handling(self):
        """Testa o tratamento de erros"""
        # Simular um erro na API
        with patch.object(LNDClient, '_request', return_value={"error": "Erro simulado"}):
            result = self.client.get_info()
            self.assertIn("error", result)
            self.assertEqual(result["error"], "Erro simulado")

if __name__ == "__main__":
    unittest.main()
