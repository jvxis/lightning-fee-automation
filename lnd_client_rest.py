#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cliente LND usando API REST
"""

import os
import json
import base64
import requests
from urllib.parse import urljoin

class LNDClient:
    """Cliente para interagir com a API REST do LND"""
    
    def __init__(self, lnd_host="jvx-minipc01", lnd_port=8080, 
                 cert_path=None, macaroon_path=None, dev_mode=False):
        """
        Inicializa o cliente LND
        
        Args:
            lnd_host (str): Host do LND
            lnd_port (int): Porta REST do LND
            cert_path (str): Caminho para o certificado TLS
            macaroon_path (str): Caminho para o macaroon de admin
            dev_mode (bool): Modo de desenvolvimento (simula respostas)
        """
        self.lnd_host = lnd_host
        self.lnd_port = lnd_port
        self.base_url = f"https://{lnd_host}:{lnd_port}/v1/"
        
        # Verificar modo de desenvolvimento
        self.dev_mode = dev_mode or os.environ.get("LND_DEV_MODE") == "1"
        
        if not self.dev_mode:
            # Carregar certificado TLS
            if cert_path is None:
                cert_path = os.path.expanduser("~/.lnd/tls.cert")
            self.cert_path = os.path.expanduser(cert_path)
            
            # Carregar macaroon
            if macaroon_path is None:
                macaroon_path = os.path.expanduser("~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon")
            self.macaroon_path = os.path.expanduser(macaroon_path)
            
            # Verificar se os arquivos existem
            if not os.path.exists(self.cert_path):
                raise FileNotFoundError(f"Certificado TLS não encontrado: {self.cert_path}")
            if not os.path.exists(self.macaroon_path):
                raise FileNotFoundError(f"Macaroon não encontrado: {self.macaroon_path}")
            
            # Ler macaroon
            with open(self.macaroon_path, 'rb') as f:
                macaroon_bytes = f.read()
            self.macaroon = base64.b64encode(macaroon_bytes).decode('ascii')
            
            # Configurar sessão
            self.session = requests.Session()
            self.session.verify = self.cert_path
            self.headers = {
                'Grpc-Metadata-macaroon': self.macaroon,
                'Content-Type': 'application/json'
            }
    
    def _request(self, method, endpoint, params=None, data=None):
        """
        Faz uma requisição para a API REST do LND
        
        Args:
            method (str): Método HTTP (GET, POST, DELETE)
            endpoint (str): Endpoint da API
            params (dict): Parâmetros da query string
            data (dict): Dados para enviar no corpo da requisição
            
        Returns:
            dict: Resposta da API
        """
        if self.dev_mode:
            return self._simulate_response(endpoint, params, data)
        
        url = urljoin(self.base_url, endpoint)
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=self.headers, params=params)
            elif method == 'POST':
                response = self.session.post(url, headers=self.headers, json=data)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=self.headers, params=params)
            else:
                return {"error": f"Método não suportado: {method}"}
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def _simulate_response(self, endpoint, params=None, data=None):
        """
        Simula uma resposta da API para o modo de desenvolvimento
        
        Args:
            endpoint (str): Endpoint da API
            params (dict): Parâmetros da query string
            data (dict): Dados para enviar no corpo da requisição
            
        Returns:
            dict: Resposta simulada
        """
        # Simular getinfo
        if endpoint == 'getinfo':
            return {
                "identity_pubkey": "03a5a9ecbafb4ca0d9c7b508cfd7e3e153d4168f61d5d71efb9f5a4797f7f25722",
                "alias": "my-lnd-node",
                "num_active_channels": 5,
                "num_pending_channels": 1,
                "num_peers": 8,
                "block_height": 800000,
                "block_hash": "000000000000000000071894abfc1f2b5d07a7ef6fd5fe9e5a0d5a0c0edc2e7d",
                "synced_to_chain": True,
                "testnet": False,
                "chains": [
                    {
                        "chain": "bitcoin",
                        "network": "mainnet"
                    }
                ],
                "version": "0.15.5-beta"
            }
        
        # Simular listchannels
        elif endpoint == 'channels':
            return {
                "channels": [
                    {
                        "active": True,
                        "remote_pubkey": "02a5a9ecbafb4ca0d9c7b508cfd7e3e153d4168f61d5d71efb9f5a4797f7f25722",
                        "channel_point": "6aef8ad9c97d9b9a8853b59e101d1a57f6f3ea19ccb2a4c8f16f51a6ae84094d:0",
                        "chan_id": "724725106597969920",
                        "capacity": "1000000",
                        "local_balance": "600000",
                        "remote_balance": "400000",
                        "commit_fee": "200",
                        "commit_weight": "724",
                        "fee_per_kw": "253",
                        "unsettled_balance": "0",
                        "total_satoshis_sent": "100000",
                        "total_satoshis_received": "50000",
                        "num_updates": "10",
                        "pending_htlcs": []
                    },
                    {
                        "active": True,
                        "remote_pubkey": "03b5a9ecbafb4ca0d9c7b508cfd7e3e153d4168f61d5d71efb9f5a4797f7f25722",
                        "channel_point": "7aef8ad9c97d9b9a8853b59e101d1a57f6f3ea19ccb2a4c8f16f51a6ae84094d:1",
                        "chan_id": "724725106597969921",
                        "capacity": "2000000",
                        "local_balance": "800000",
                        "remote_balance": "1200000",
                        "commit_fee": "300",
                        "commit_weight": "724",
                        "fee_per_kw": "253",
                        "unsettled_balance": "0",
                        "total_satoshis_sent": "200000",
                        "total_satoshis_received": "100000",
                        "num_updates": "20",
                        "pending_htlcs": []
                    }
                ]
            }
        
        # Simular getchaninfo
        elif endpoint.startswith('graph/edge/'):
            chan_id = endpoint.split('/')[-1]
            return {
                "channel_id": chan_id,
                "chan_point": "6aef8ad9c97d9b9a8853b59e101d1a57f6f3ea19ccb2a4c8f16f51a6ae84094d:0",
                "last_update": 1650000000,
                "node1_pub": "03a5a9ecbafb4ca0d9c7b508cfd7e3e153d4168f61d5d71efb9f5a4797f7f25722",
                "node2_pub": "02a5a9ecbafb4ca0d9c7b508cfd7e3e153d4168f61d5d71efb9f5a4797f7f25722",
                "capacity": "1000000",
                "node1_policy": {
                    "time_lock_delta": 40,
                    "min_htlc": "1000",
                    "fee_base_msat": "1000",
                    "fee_rate_milli_msat": "1",
                    "disabled": False,
                    "max_htlc_msat": "990000000",
                    "last_update": 1650000000
                },
                "node2_policy": {
                    "time_lock_delta": 40,
                    "min_htlc": "1000",
                    "fee_base_msat": "1500",
                    "fee_rate_milli_msat": "2",
                    "disabled": False,
                    "max_htlc_msat": "990000000",
                    "last_update": 1650000000
                }
            }
        
        # Simular updatechanpolicy
        elif endpoint == 'chanpolicy':
            return {
                "failed_updates": []
            }
        
        # Resposta padrão para endpoints não simulados
        return {"error": f"Endpoint não simulado: {endpoint}"}
    
    def get_info(self):
        """
        Obtém informações do node
        
        Returns:
            dict: Informações do node
        """
        return self._request('GET', 'getinfo')
    
    def list_channels(self):
        """
        Lista todos os canais ativos
        
        Returns:
            dict: Lista de canais
        """
        return self._request('GET', 'channels')
    
    def get_channel_info(self, chan_id):
        """
        Obtém informações de um canal específico
        
        Args:
            chan_id (str): ID do canal
            
        Returns:
            dict: Informações do canal
        """
        return self._request('GET', f'graph/edge/{chan_id}')
    
    def update_channel_policy(self, global_update=False, chan_point=None, 
                             base_fee_msat=1000, fee_rate=0.000001, time_lock_delta=40):
        """
        Atualiza a política de taxas de um canal
        
        Args:
            global_update (bool): Se True, atualiza todos os canais
            chan_point (dict): Ponto do canal (funding_txid_str e output_index)
            base_fee_msat (int): Taxa base em milisatoshis
            fee_rate (float): Taxa proporcional (ex: 0.000001 = 1 ppm)
            time_lock_delta (int): Delta de time lock
            
        Returns:
            dict: Resultado da atualização
        """
        # Converter fee_rate para fee_rate_ppm (partes por milhão)
        fee_rate_ppm = int(fee_rate * 1000000)
        
        data = {
            "base_fee_msat": str(base_fee_msat),
            "fee_rate_ppm": fee_rate_ppm,
            "time_lock_delta": time_lock_delta
        }
        
        if not global_update and chan_point:
            data["chan_point"] = {
                "funding_txid_str": chan_point["funding_txid_str"],
                "output_index": chan_point["output_index"]
            }
        
        return self._request('POST', 'chanpolicy', data=data)

# Exemplo de uso
if __name__ == "__main__":
    # Criar cliente
    client = LNDClient(dev_mode=True)
    
    # Obter informações do node
    info = client.get_info()
    print("Informações do node:", json.dumps(info, indent=2))
    
    # Listar canais
    channels = client.list_channels()
    print("Canais:", json.dumps(channels, indent=2))
    
    # Obter informações de um canal específico
    if channels.get("channels"):
        chan_id = channels["channels"][0]["chan_id"]
        chan_info = client.get_channel_info(chan_id)
        print(f"Informações do canal {chan_id}:", json.dumps(chan_info, indent=2))
    
    # Atualizar política de taxas
    result = client.update_channel_policy(global_update=True, base_fee_msat=1500, fee_rate=0.000002)
    print("Resultado da atualização:", json.dumps(result, indent=2))
