#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de teste integrado para a aplicação de automação de taxas
"""

import os
import sys
import time
import unittest

# Adicionar diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar os módulos a serem testados
from lnd_client_rest import LNDClient
from fee_manager import FeeManager
from web.app import app

class TestIntegration(unittest.TestCase):
    """Testes de integração para a aplicação completa"""
    
    def setUp(self):
        """Configuração para cada teste"""
        # Ativar modo de desenvolvimento para simular respostas
        os.environ["LND_DEV_MODE"] = "1"
        
        # Inicializar componentes
        self.lnd_client = LNDClient()
        self.fee_manager = FeeManager(lnd_client=self.lnd_client)
        
        # Configurar o cliente de teste para a API web
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Injetar componentes reais na aplicação
        app.fee_manager = self.fee_manager
        app.lnd_client = self.lnd_client
    
    def test_full_workflow(self):
        """Testa o fluxo completo da aplicação"""
        # 1. Verificar se o cliente LND está funcionando
        info = self.lnd_client.get_info()
        self.assertIsNotNone(info)
        self.assertIn("identity_pubkey", info)
        
        # 2. Verificar se o gerenciador de taxas está funcionando
        self.fee_manager.load_config()
        status = self.fee_manager.get_status()
        self.assertIsNotNone(status)
        self.assertIn("running", status)
        
        # 3. Testar atualização de taxas
        result = self.fee_manager.update_all_channels()
        self.assertEqual(result["success"], True)
        
        # 4. Testar início e parada da automação
        self.fee_manager.start()
        self.assertTrue(self.fee_manager.running)
        time.sleep(1)  # Pequena pausa para garantir que a thread inicie
        self.fee_manager.stop()
        self.assertFalse(self.fee_manager.running)
        
        # 5. Testar API web - Obter informações do node
        response = self.client.get('/api/node/info')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("identity_pubkey", data)
        
        # 6. Testar API web - Obter canais
        response = self.client.get('/api/channels')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("channels", data)
        
        # 7. Testar API web - Obter configuração
        response = self.client.get('/api/config')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("fee_strategy", data)
        
        # 8. Testar API web - Atualizar configuração
        new_config = {
            "fee_strategy": "competitive",
            "update_interval_seconds": 1800
        }
        
        response = self.client.post('/api/config', json=new_config)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["success"], True)
        
        # Verificar se a configuração foi atualizada
        self.assertEqual(self.fee_manager.config["fee_strategy"], "competitive")
        self.assertEqual(self.fee_manager.config["update_interval_seconds"], 1800)
        
        # 9. Testar API web - Iniciar automação
        response = self.client.post('/api/fees/start')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["success"], True)
        self.assertTrue(self.fee_manager.running)
        
        # 10. Testar API web - Parar automação
        response = self.client.post('/api/fees/stop')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["success"], True)
        self.assertFalse(self.fee_manager.running)
        
        # 11. Testar API web - Atualizar taxas
        response = self.client.post('/api/fees/update')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["success"], True)
        
        # 12. Testar renderização das páginas
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/channels')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/settings')
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
