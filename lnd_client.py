#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LND Client para automação de taxas
Este módulo fornece uma interface para interagir com a API do LND
"""

import os
import codecs
import grpc
import base64
import json
import requests
from typing import Dict, List, Optional, Tuple, Union

# Importações para gRPC (serão necessárias quando o cliente for usado com o LND real)
# Estas importações serão descomentadas quando o script for usado em produção
"""
import rpc_pb2 as ln
import rpc_pb2_grpc as lnrpc
import router_pb2 as router
import router_pb2_grpc as routerrpc
"""

class LNDClient:
    """Cliente para interagir com a API do LND"""
    
    def __init__(self, lnd_dir: str = None, macaroon_path: str = None, 
                 tls_cert_path: str = None, lnd_host: str = "localhost", 
                 lnd_port: int = 8080, use_rest: bool = True):
        """
        Inicializa o cliente LND
        
        Args:
            lnd_dir: Diretório do LND (padrão: ~/.lnd)
            macaroon_path: Caminho para o arquivo macaroon (padrão: ~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon)
            tls_cert_path: Caminho para o certificado TLS (padrão: ~/.lnd/tls.cert)
            lnd_host: Host do LND (padrão: localhost)
            lnd_port: Porta do LND (padrão: 8080 para REST, 10009 para gRPC)
            use_rest: Se True, usa a API REST, caso contrário usa gRPC
        """
        # Definir diretório padrão do LND se não for fornecido
        if lnd_dir is None:
            lnd_dir = os.path.expanduser("~/.lnd")
        
        # Definir caminhos padrão se não forem fornecidos
        if macaroon_path is None:
            macaroon_path = os.path.join(lnd_dir, "data/chain/bitcoin/mainnet/admin.macaroon")
        if tls_cert_path is None:
            tls_cert_path = os.path.join(lnd_dir, "tls.cert")
        
        self.lnd_dir = lnd_dir
        self.macaroon_path = macaroon_path
        self.tls_cert_path = tls_cert_path
        self.lnd_host = lnd_host
        self.lnd_port = lnd_port
        self.use_rest = use_rest
        
        # Configurar cliente REST ou gRPC
        if use_rest:
            self.rest_url = f"https://{lnd_host}:{lnd_port}/v1"
            self.macaroon_header = self._get_macaroon_header()
        else:
            # Configuração gRPC será implementada quando necessário
            pass
    
    def _get_macaroon_header(self) -> Dict[str, str]:
        """
        Obtém o cabeçalho de autenticação com o macaroon
        
        Returns:
            Dicionário com o cabeçalho de autenticação
        """
        try:
            with open(self.macaroon_path, 'rb') as f:
                macaroon_bytes = f.read()
            macaroon = codecs.encode(macaroon_bytes, 'hex')
            return {'Grpc-Metadata-macaroon': macaroon.decode()}
        except Exception as e:
            print(f"Erro ao ler macaroon: {e}")
            # Em modo de desenvolvimento, retorna um cabeçalho vazio
            return {}
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """
        Faz uma requisição REST para o LND
        
        Args:
            method: Método HTTP (GET, POST, DELETE)
            endpoint: Endpoint da API
            params: Parâmetros da query string
            data: Dados para enviar no corpo da requisição
            
        Returns:
            Resposta da API como um dicionário
        """
        url = f"{self.rest_url}/{endpoint}"
        
        try:
            # Em modo de desenvolvimento, simula a resposta
            if os.environ.get("LND_DEV_MODE") == "1":
                return self._simulate_response(method, endpoint, params, data)
            
            # Em produção, faz a requisição real
            with open(self.tls_cert_path, 'rb') as f:
                cert = f.read()
            
            if method == 'GET':
                response = requests.get(url, headers=self.macaroon_header, 
                                       params=params, verify=cert)
            elif method == 'POST':
                response = requests.post(url, headers=self.macaroon_header, 
                                        json=data, params=params, verify=cert)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.macaroon_header, 
                                          params=params, verify=cert)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erro na requisição {method} {endpoint}: {e}")
            return {"error": str(e)}
    
    def _simulate_response(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """
        Simula uma resposta da API para desenvolvimento
        
        Args:
            method: Método HTTP
            endpoint: Endpoint da API
            params: Parâmetros da query string
            data: Dados do corpo da requisição
            
        Returns:
            Resposta simulada como um dicionário
        """
        # Simulações para diferentes endpoints
        if endpoint == "channels":
            return {
                "channels": [
                    {
                        "active": True,
                        "remote_pubkey": "02a5d96b8f7e7a5f148b8d0db11a2ef6c2d2e4841f075db9d2433d010fbf5f9e93",
                        "channel_point": "7e6090cae6e25dd580c03ad5328f64ac17ee8b30ee3990aef3e357b4b0f35142:0",
                        "chan_id": "724725106597969921",
                        "capacity": "5000000",
                        "local_balance": "2500000",
                        "remote_balance": "2490000",
                        "commit_fee": "10000",
                        "commit_weight": "600",
                        "fee_per_kw": "12500",
                        "unsettled_balance": "0",
                        "total_satoshis_sent": "100000",
                        "total_satoshis_received": "50000",
                        "num_updates": "10",
                        "pending_htlcs": [],
                        "csv_delay": 144,
                        "private": False,
                        "initiator": True,
                        "chan_status_flags": "ChanStatusNormal",
                        "local_chan_reserve_sat": "50000",
                        "remote_chan_reserve_sat": "50000",
                        "static_remote_key": True,
                        "lifetime": "10000",
                        "uptime": "9000",
                        "close_address": "",
                        "push_amount_sat": "0",
                        "thaw_height": 0,
                        "local_constraints": {
                            "csv_delay": 144,
                            "chan_reserve_sat": "50000",
                            "dust_limit_sat": "573",
                            "max_pending_amt_msat": "5000000000",
                            "min_htlc_msat": "1000",
                            "max_accepted_htlcs": 483
                        },
                        "remote_constraints": {
                            "csv_delay": 144,
                            "chan_reserve_sat": "50000",
                            "dust_limit_sat": "573",
                            "max_pending_amt_msat": "5000000000",
                            "min_htlc_msat": "1000",
                            "max_accepted_htlcs": 483
                        }
                    },
                    {
                        "active": True,
                        "remote_pubkey": "03b424886b71c9de399b3996c19eadf6e7e0eef2ce8ffd4e7c7aba1d33fb47d712",
                        "channel_point": "1337e6090cae6e25dd580c03ad5328f64ac17ee8b30ee3990aef3e357b4b0f35:1",
                        "chan_id": "724725106597969922",
                        "capacity": "10000000",
                        "local_balance": "4000000",
                        "remote_balance": "5990000",
                        "commit_fee": "10000",
                        "commit_weight": "600",
                        "fee_per_kw": "12500",
                        "unsettled_balance": "0",
                        "total_satoshis_sent": "200000",
                        "total_satoshis_received": "300000",
                        "num_updates": "15",
                        "pending_htlcs": [],
                        "csv_delay": 144,
                        "private": False,
                        "initiator": True,
                        "chan_status_flags": "ChanStatusNormal",
                        "local_chan_reserve_sat": "100000",
                        "remote_chan_reserve_sat": "100000",
                        "static_remote_key": True,
                        "lifetime": "20000",
                        "uptime": "18000",
                        "close_address": "",
                        "push_amount_sat": "0",
                        "thaw_height": 0,
                        "local_constraints": {
                            "csv_delay": 144,
                            "chan_reserve_sat": "100000",
                            "dust_limit_sat": "573",
                            "max_pending_amt_msat": "10000000000",
                            "min_htlc_msat": "1000",
                            "max_accepted_htlcs": 483
                        },
                        "remote_constraints": {
                            "csv_delay": 144,
                            "chan_reserve_sat": "100000",
                            "dust_limit_sat": "573",
                            "max_pending_amt_msat": "10000000000",
                            "min_htlc_msat": "1000",
                            "max_accepted_htlcs": 483
                        }
                    }
                ]
            }
        elif endpoint == "graph/edge":
            return {
                "channel_id": "724725106597969921",
                "chan_point": "7e6090cae6e25dd580c03ad5328f64ac17ee8b30ee3990aef3e357b4b0f35142:0",
                "last_update": 1650000000,
                "node1_pub": "02a5d96b8f7e7a5f148b8d0db11a2ef6c2d2e4841f075db9d2433d010fbf5f9e93",
                "node2_pub": "03b424886b71c9de399b3996c19eadf6e7e0eef2ce8ffd4e7c7aba1d33fb47d712",
                "capacity": "5000000",
                "node1_policy": {
                    "time_lock_delta": 40,
                    "min_htlc": "1000",
                    "fee_base_msat": "1000",
                    "fee_rate_milli_msat": "1",
                    "disabled": False,
                    "max_htlc_msat": "4950000000",
                    "last_update": 1650000000
                },
                "node2_policy": {
                    "time_lock_delta": 40,
                    "min_htlc": "1000",
                    "fee_base_msat": "2000",
                    "fee_rate_milli_msat": "2",
                    "disabled": False,
                    "max_htlc_msat": "4950000000",
                    "last_update": 1650000000
                }
            }
        elif endpoint == "chanpolicy" and method == "POST":
            return {
                "failed_updates": []
            }
        elif endpoint == "getinfo":
            return {
                "version": "0.15.0-beta",
                "commit_hash": "0123456789abcdef",
                "identity_pubkey": "03b424886b71c9de399b3996c19eadf6e7e0eef2ce8ffd4e7c7aba1d33fb47d712",
                "alias": "my-node",
                "color": "#3399ff",
                "num_pending_channels": 0,
                "num_active_channels": 2,
                "num_peers": 5,
                "block_height": 700000,
                "block_hash": "000000000000000000000000000000000000000000000000000000000000000",
                "best_header_timestamp": 1650000000,
                "synced_to_chain": True,
                "synced_to_graph": True,
                "chains": [
                    {
                        "chain": "bitcoin",
                        "network": "mainnet"
                    }
                ],
                "uris": [
                    "03b424886b71c9de399b3996c19eadf6e7e0eef2ce8ffd4e7c7aba1d33fb47d712@127.0.0.1:9735"
                ]
            }
        
        # Resposta padrão para endpoints não simulados
        return {"error": "Endpoint não simulado"}
    
    def get_info(self) -> Dict:
        """
        Obtém informações gerais sobre o node
        
        Returns:
            Informações do node
        """
        return self._request('GET', 'getinfo')
    
    def list_channels(self, active_only: bool = True, inactive_only: bool = False, 
                     public_only: bool = False, private_only: bool = False) -> Dict:
        """
        Lista os canais do node
        
        Args:
            active_only: Se True, lista apenas canais ativos
            inactive_only: Se True, lista apenas canais inativos
            public_only: Se True, lista apenas canais públicos
            private_only: Se True, lista apenas canais privados
            
        Returns:
            Lista de canais
        """
        params = {
            'active_only': str(active_only).lower(),
            'inactive_only': str(inactive_only).lower(),
            'public_only': str(public_only).lower(),
            'private_only': str(private_only).lower()
        }
        return self._request('GET', 'channels', params=params)
    
    def get_channel_info(self, chan_id: str) -> Dict:
        """
        Obtém informações detalhadas sobre um canal específico
        
        Args:
            chan_id: ID do canal
            
        Returns:
            Informações do canal
        """
        return self._request('GET', f'graph/edge/{chan_id}')
    
    def update_channel_policy(self, global_update: bool = False, chan_point: Dict = None,
                             base_fee_msat: int = None, fee_rate: float = None,
                             time_lock_delta: int = None, max_htlc_msat: int = None,
                             min_htlc_msat: int = None) -> Dict:
        """
        Atualiza a política de taxas de um canal ou de todos os canais
        
        Args:
            global_update: Se True, atualiza todos os canais
            chan_point: Ponto do canal (funding_txid_str e output_index)
            base_fee_msat: Taxa base em milisatoshis
            fee_rate: Taxa proporcional (0.000001 a 1.0)
            time_lock_delta: Delta de timelock para HTLCs
            max_htlc_msat: Tamanho máximo de HTLC em milisatoshis
            min_htlc_msat: Tamanho mínimo de HTLC em milisatoshis
            
        Returns:
            Resultado da atualização
        """
        data = {
            'global': global_update
        }
        
        if chan_point:
            data['chan_point'] = chan_point
        
        if base_fee_msat is not None:
            data['base_fee_msat'] = str(base_fee_msat)
        
        if fee_rate is not None:
            data['fee_rate'] = fee_rate
        
        if time_lock_delta is not None:
            data['time_lock_delta'] = time_lock_delta
        
        if max_htlc_msat is not None:
            data['max_htlc_msat'] = str(max_htlc_msat)
        
        if min_htlc_msat is not None:
            data['min_htlc_msat'] = str(min_htlc_msat)
            data['min_htlc_msat_specified'] = True
        
        return self._request('POST', 'chanpolicy', data=data)
    
    def get_forwarding_history(self, start_time: int = None, end_time: int = None,
                              index_offset: int = 0, max_events: int = 100) -> Dict:
        """
        Obtém o histórico de encaminhamento de pagamentos
        
        Args:
            start_time: Timestamp de início (Unix timestamp)
            end_time: Timestamp de fim (Unix timestamp)
            index_offset: Índice de início para paginação
            max_events: Número máximo de eventos a retornar
            
        Returns:
            Histórico de encaminhamento
        """
        params = {
            'index_offset': index_offset,
            'max_events': max_events
        }
        
        if start_time:
            params['start_time'] = start_time
        
        if end_time:
            params['end_time'] = end_time
        
        return self._request('GET', 'switch', params=params)


if __name__ == "__main__":
    # Exemplo de uso
    client = LNDClient()
    
    # Definir modo de desenvolvimento para simular respostas
    os.environ["LND_DEV_MODE"] = "1"
    
    # Obter informações do node
    info = client.get_info()
    print("Informações do node:")
    print(json.dumps(info, indent=2))
    
    # Listar canais
    channels = client.list_channels()
    print("\nCanais:")
    print(json.dumps(channels, indent=2))
    
    # Obter informações de um canal específico
    if channels.get("channels"):
        chan_id = channels["channels"][0]["chan_id"]
        chan_info = client.get_channel_info(chan_id)
        print(f"\nInformações do canal {chan_id}:")
        print(json.dumps(chan_info, indent=2))
    
    # Exemplo de atualização de política de taxas
    update_result = client.update_channel_policy(
        global_update=True,
        base_fee_msat=1000,
        fee_rate=0.000001,
        time_lock_delta=40
    )
    print("\nResultado da atualização de política:")
    print(json.dumps(update_result, indent=2))
