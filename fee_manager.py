#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gerenciador de Taxas para LND
Este módulo implementa a lógica de automação de taxas para o LND
"""

import os
import time
import json
import logging
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import threading
import statistics

# Importar o cliente LND
from lnd_client_rest import LNDClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fee_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fee_manager")

class FeeManager:
    """Gerenciador de taxas para o LND"""
    
    def __init__(self, lnd_client: LNDClient, config_path: str = "fee_config.json"):
        """
        Inicializa o gerenciador de taxas
        
        Args:
            lnd_client: Cliente LND para interagir com a API
            config_path: Caminho para o arquivo de configuração
        """
        self.lnd_client = lnd_client
        self.config_path = config_path
        self.config = self._load_config()
        self.channel_stats = {}
        self.peer_fees = {}
        self.running = False
        self.thread = None
        
        # Carregar estatísticas anteriores se existirem
        self._load_stats()
    
    def _load_config(self) -> Dict:
        """
        Carrega a configuração do arquivo
        
        Returns:
            Configuração como um dicionário
        """
        default_config = {
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
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Mesclar com configurações padrão para garantir que todas as chaves existam
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                # Salvar configuração padrão se o arquivo não existir
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, indent=2, sort_keys=True, f)
                return default_config
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            return default_config
    
    def save_config(self) -> None:
        """Salva a configuração atual no arquivo"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, indent=2, sort_keys=True, f)
            logger.info("Configuração salva com sucesso")
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
    
    def _load_stats(self) -> None:
        """Carrega estatísticas anteriores de canais e peers"""
        try:
            if os.path.exists("channel_stats.json"):
                with open("channel_stats.json", 'r') as f:
                    self.channel_stats = json.load(f)
            
            if os.path.exists("peer_fees.json"):
                with open("peer_fees.json", 'r') as f:
                    self.peer_fees = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar estatísticas: {e}")
    
    def _save_stats(self) -> None:
        """Salva estatísticas atuais de canais e peers"""
        try:
            with open("channel_stats.json", 'w') as f:
                json.dump(self.channel_stats, indent=2, f)
            
            with open("peer_fees.json", 'w') as f:
                json.dump(self.peer_fees, indent=2, f)
        except Exception as e:
            logger.error(f"Erro ao salvar estatísticas: {e}")
    
    def collect_channel_data(self) -> None:
        """Coleta dados sobre os canais e atualiza as estatísticas"""
        try:
            # Obter lista de canais
            channels_response = self.lnd_client.list_channels()
            if "error" in channels_response:
                logger.error(f"Erro ao listar canais: {channels_response['error']}")
                return
            
            channels = channels_response.get("channels", [])
            timestamp = int(time.time())
            
            for channel in channels:
                chan_id = channel["chan_id"]
                
                # Pular canais excluídos
                if chan_id in self.config["excluded_channels"]:
                    continue
                
                # Pular canais não incluídos se a lista de canais habilitados não estiver vazia
                if self.config["enabled_channels"] and chan_id not in self.config["enabled_channels"]:
                    continue
                
                # Inicializar estatísticas do canal se não existirem
                if chan_id not in self.channel_stats:
                    self.channel_stats[chan_id] = {
                        "capacity": int(channel["capacity"]),
                        "remote_pubkey": channel["remote_pubkey"],
                        "flow_history": [],
                        "fee_history": []
                    }
                
                # Atualizar capacidade se mudou
                self.channel_stats[chan_id]["capacity"] = int(channel["capacity"])
                
                # Calcular fluxo atual (entrada e saída)
                local_balance = int(channel["local_balance"])
                remote_balance = int(channel["remote_balance"])
                capacity = int(channel["capacity"])
                
                # Calcular métricas de fluxo
                inbound_ratio = remote_balance / capacity if capacity > 0 else 0
                outbound_ratio = local_balance / capacity if capacity > 0 else 0
                balance_ratio = local_balance / (local_balance + remote_balance) if (local_balance + remote_balance) > 0 else 0.5
                
                # Obter histórico de encaminhamento para este canal
                # Em um ambiente real, isso seria obtido da API do LND
                # Aqui estamos simulando com dados fictícios
                forwarding_volume_in = int(channel.get("total_satoshis_received", 0))
                forwarding_volume_out = int(channel.get("total_satoshis_sent", 0))
                
                # Adicionar dados de fluxo ao histórico
                flow_data = {
                    "timestamp": timestamp,
                    "local_balance": local_balance,
                    "remote_balance": remote_balance,
                    "inbound_ratio": inbound_ratio,
                    "outbound_ratio": outbound_ratio,
                    "balance_ratio": balance_ratio,
                    "forwarding_volume_in": forwarding_volume_in,
                    "forwarding_volume_out": forwarding_volume_out
                }
                
                self.channel_stats[chan_id]["flow_history"].append(flow_data)
                
                # Limitar o histórico a 30 dias (assumindo uma atualização por hora)
                max_history = 24 * 30
                if len(self.channel_stats[chan_id]["flow_history"]) > max_history:
                    self.channel_stats[chan_id]["flow_history"] = self.channel_stats[chan_id]["flow_history"][-max_history:]
                
                # Obter informações detalhadas do canal para ver as taxas atuais
                chan_info = self.lnd_client.get_channel_info(chan_id)
                if "error" not in chan_info:
                    # Determinar qual política é a nossa (node1 ou node2)
                    our_pubkey = self.lnd_client.get_info().get("identity_pubkey", "")
                    
                    if chan_info.get("node1_pub") == our_pubkey:
                        our_policy = chan_info.get("node1_policy", {})
                        their_policy = chan_info.get("node2_policy", {})
                    else:
                        our_policy = chan_info.get("node2_policy", {})
                        their_policy = chan_info.get("node1_policy", {})
                    
                    # Registrar taxas atuais
                    if our_policy:
                        fee_data = {
                            "timestamp": timestamp,
                            "base_fee_msat": int(our_policy.get("fee_base_msat", 0)),
                            "fee_rate": float(our_policy.get("fee_rate_milli_msat", 0)) / 1000000,
                            "time_lock_delta": our_policy.get("time_lock_delta", 40)
                        }
                        
                        self.channel_stats[chan_id]["fee_history"].append(fee_data)
                        
                        # Limitar o histórico de taxas
                        if len(self.channel_stats[chan_id]["fee_history"]) > max_history:
                            self.channel_stats[chan_id]["fee_history"] = self.channel_stats[chan_id]["fee_history"][-max_history:]
                    
                    # Registrar taxas do peer
                    if their_policy:
                        peer_pubkey = channel["remote_pubkey"]
                        if peer_pubkey not in self.peer_fees:
                            self.peer_fees[peer_pubkey] = []
                        
                        peer_fee_data = {
                            "timestamp": timestamp,
                            "chan_id": chan_id,
                            "base_fee_msat": int(their_policy.get("fee_base_msat", 0)),
                            "fee_rate": float(their_policy.get("fee_rate_milli_msat", 0)) / 1000000,
                            "time_lock_delta": their_policy.get("time_lock_delta", 40)
                        }
                        
                        self.peer_fees[peer_pubkey].append(peer_fee_data)
                        
                        # Limitar o histórico de taxas dos peers
                        if len(self.peer_fees[peer_pubkey]) > max_history:
                            self.peer_fees[peer_pubkey] = self.peer_fees[peer_pubkey][-max_history:]
            
            # Salvar estatísticas atualizadas
            self._save_stats()
            logger.info(f"Dados de {len(channels)} canais coletados e salvos")
            
        except Exception as e:
            logger.error(f"Erro ao coletar dados dos canais: {e}")
    
    def calculate_optimal_fees(self, chan_id: str) -> Dict:
        """
        Calcula as taxas ótimas para um canal com base no fluxo e nas taxas dos peers
        
        Args:
            chan_id: ID do canal
            
        Returns:
            Dicionário com as taxas ótimas
        """
        if chan_id not in self.channel_stats:
            logger.warning(f"Canal {chan_id} não encontrado nas estatísticas")
            return {
                "base_fee_msat": self.config["min_base_fee_msat"],
                "fee_rate": self.config["min_fee_rate"],
                "time_lock_delta": self.config["time_lock_delta"]
            }
        
        channel = self.channel_stats[chan_id]
        
        # Obter dados de fluxo mais recentes
        flow_data = channel["flow_history"][-1] if channel["flow_history"] else None
        
        if not flow_data:
            logger.warning(f"Sem dados de fluxo para o canal {chan_id}")
            return {
                "base_fee_msat": self.config["min_base_fee_msat"],
                "fee_rate": self.config["min_fee_rate"],
                "time_lock_delta": self.config["time_lock_delta"]
            }
        
        # Obter taxas atuais do peer
        peer_pubkey = channel["remote_pubkey"]
        peer_fee_data = None
        
        if peer_pubkey in self.peer_fees and self.peer_fees[peer_pubkey]:
            # Encontrar a taxa mais recente para este canal específico
            for fee_data in reversed(self.peer_fees[peer_pubkey]):
                if fee_data["chan_id"] == chan_id:
                    peer_fee_data = fee_data
                    break
        
        # Calcular taxas com base na estratégia selecionada
        strategy = self.config["fee_strategy"]
        
        if strategy == "balanced":
            return self._calculate_balanced_fees(chan_id, flow_data, peer_fee_data)
        elif strategy == "competitive":
            return self._calculate_competitive_fees(chan_id, flow_data, peer_fee_data)
        elif strategy == "profitable":
            return self._calculate_profitable_fees(chan_id, flow_data, peer_fee_data)
        else:
            logger.warning(f"Estratégia desconhecida: {strategy}, usando 'balanced'")
            return self._calculate_balanced_fees(chan_id, flow_data, peer_fee_data)
    
    def _calculate_balanced_fees(self, chan_id: str, flow_data: Dict, peer_fee_data: Dict) -> Dict:
        """
        Calcula taxas balanceadas que consideram tanto o fluxo quanto as taxas dos peers
        
        Args:
            chan_id: ID do canal
            flow_data: Dados de fluxo do canal
            peer_fee_data: Dados de taxas do peer
            
        Returns:
            Dicionário com as taxas calculadas
        """
        # Parâmetros de configuração
        min_base_fee = self.config["min_base_fee_msat"]
        max_base_fee = self.config["max_base_fee_msat"]
        min_fee_rate = self.config["min_fee_rate"]
        max_fee_rate = self.config["max_fee_rate"]
        flow_weight = self.config["flow_weight"]
        peer_weight = self.config["peer_weight"]
        high_flow = self.config["high_flow_threshold"]
        low_flow = self.config["low_flow_threshold"]
        
        # Calcular fator de fluxo
        inbound_ratio = flow_data["inbound_ratio"]
        outbound_ratio = flow_data["outbound_ratio"]
        
        # Se o canal está desequilibrado (muito inbound ou muito outbound)
        # ajustar as taxas para incentivar o fluxo na direção oposta
        if inbound_ratio > high_flow:
            # Muito inbound, reduzir taxas para incentivar outbound
            flow_factor = 0.2
        elif outbound_ratio > high_flow:
            # Muito outbound, aumentar taxas para desincentivar mais outbound
            flow_factor = 0.8
        elif inbound_ratio < low_flow:
            # Pouco inbound, aumentar taxas para preservar liquidez outbound
            flow_factor = 0.7
        elif outbound_ratio < low_flow:
            # Pouco outbound, reduzir taxas para atrair inbound
            flow_factor = 0.3
        else:
            # Canal bem balanceado, usar taxas moderadas
            flow_factor = 0.5
        
        # Calcular fator de peer
        peer_factor = 0.5  # Valor padrão
        
        if peer_fee_data:
            peer_base_fee = peer_fee_data["base_fee_msat"]
            peer_fee_rate = peer_fee_data["fee_rate"]
            
            # Normalizar as taxas do peer em relação aos nossos limites
            norm_peer_base_fee = (peer_base_fee - min_base_fee) / (max_base_fee - min_base_fee)
            norm_peer_base_fee = max(0, min(1, norm_peer_base_fee))
            
            norm_peer_fee_rate = (peer_fee_rate - min_fee_rate) / (max_fee_rate - min_fee_rate)
            norm_peer_fee_rate = max(0, min(1, norm_peer_fee_rate))
            
            # Média das taxas normalizadas do peer
            peer_factor = (norm_peer_base_fee + norm_peer_fee_rate) / 2
        
        # Combinar fatores com pesos
        combined_factor = flow_factor * flow_weight + peer_factor * peer_weight
        
        # Calcular taxas finais
        base_fee_msat = int(min_base_fee + combined_factor * (max_base_fee - min_base_fee))
        fee_rate = min_fee_rate + combined_factor * (max_fee_rate - min_fee_rate)
        
        return {
            "base_fee_msat": base_fee_msat,
            "fee_rate": fee_rate,
            "time_lock_delta": self.config["time_lock_delta"]
        }
    
    def _calculate_competitive_fees(self, chan_id: str, flow_data: Dict, peer_fee_data: Dict) -> Dict:
        """
        Calcula taxas competitivas que são ligeiramente menores que as dos peers
        
        Args:
            chan_id: ID do canal
            flow_data: Dados de fluxo do canal
            peer_fee_data: Dados de taxas do peer
            
        Returns:
            Dicionário com as taxas calculadas
        """
        # Parâmetros de configuração
        min_base_fee = self.config["min_base_fee_msat"]
        max_base_fee = self.config["max_base_fee_msat"]
        min_fee_rate = self.config["min_fee_rate"]
        max_fee_rate = self.config["max_fee_rate"]
        
        # Valores padrão
        base_fee_msat = min_base_fee
        fee_rate = min_fee_rate
        
        if peer_fee_data:
            # Definir taxas ligeiramente menores que as do peer (10% menores)
            peer_base_fee = peer_fee_data["base_fee_msat"]
            peer_fee_rate = peer_fee_data["fee_rate"]
            
            base_fee_msat = int(peer_base_fee * 0.9)
            fee_rate = peer_fee_rate * 0.9
            
            # Garantir que as taxas estejam dentro dos limites
            base_fee_msat = max(min_base_fee, min(max_base_fee, base_fee_msat))
            fee_rate = max(min_fee_rate, min(max_fee_rate, fee_rate))
        
        return {
            "base_fee_msat": base_fee_msat,
            "fee_rate": fee_rate,
            "time_lock_delta": self.config["time_lock_delta"]
        }
    
    def _calculate_profitable_fees(self, chan_id: str, flow_data: Dict, peer_fee_data: Dict) -> Dict:
        """
        Calcula taxas que maximizam o lucro com base no histórico de encaminhamento
        
        Args:
            chan_id: ID do canal
            flow_data: Dados de fluxo do canal
            peer_fee_data: Dados de taxas do peer
            
        Returns:
            Dicionário com as taxas calculadas
        """
        # Parâmetros de configuração
        min_base_fee = self.config["min_base_fee_msat"]
        max_base_fee = self.config["max_base_fee_msat"]
        min_fee_rate = self.config["min_fee_rate"]
        max_fee_rate = self.config["max_fee_rate"]
        
        # Analisar o histórico de encaminhamento para determinar a elasticidade de preço
        # Em um ambiente real, isso seria baseado em dados reais de encaminhamento
        # Aqui estamos usando uma abordagem simplificada
        
        # Verificar se há volume de encaminhamento
        forwarding_volume = flow_data.get("forwarding_volume_out", 0)
        
        if forwarding_volume > 0:
            # Canal com alto volume pode suportar taxas mais altas
            volume_factor = min(1.0, forwarding_volume / 1000000)  # Normalizar para 1M sats
        else:
            # Sem volume, usar taxas mais baixas para atrair fluxo
            volume_factor = 0.2
        
        # Calcular taxas com base no volume e nas taxas do peer
        if peer_fee_data:
            peer_base_fee = peer_fee_data["base_fee_msat"]
            peer_fee_rate = peer_fee_data["fee_rate"]
            
            # Usar taxas do peer como referência, ajustadas pelo volume
            base_fee_factor = 0.8 + (volume_factor * 0.4)  # 0.8 a 1.2 vezes a taxa do peer
            rate_factor = 0.8 + (volume_factor * 0.4)
            
            base_fee_msat = int(peer_base_fee * base_fee_factor)
            fee_rate = peer_fee_rate * rate_factor
        else:
            # Sem dados do peer, calcular com base apenas no volume
            base_fee_msat = int(min_base_fee + volume_factor * (max_base_fee - min_base_fee))
            fee_rate = min_fee_rate + volume_factor * (max_fee_rate - min_fee_rate)
        
        # Garantir que as taxas estejam dentro dos limites
        base_fee_msat = max(min_base_fee, min(max_base_fee, base_fee_msat))
        fee_rate = max(min_fee_rate, min(max_fee_rate, fee_rate))
        
        return {
            "base_fee_msat": base_fee_msat,
            "fee_rate": fee_rate,
            "time_lock_delta": self.config["time_lock_delta"]
        }
    
    def update_channel_fees(self) -> None:
        """Atualiza as taxas de todos os canais com base nas taxas ótimas calculadas"""
        try:
            # Obter lista de canais
            channels_response = self.lnd_client.list_channels()
            if "error" in channels_response:
                logger.error(f"Erro ao listar canais: {channels_response['error']}")
                return
            
            channels = channels_response.get("channels", [])
            
            for channel in channels:
                chan_id = channel["chan_id"]
                
                # Pular canais excluídos
                if chan_id in self.config["excluded_channels"]:
                    continue
                
                # Pular canais não incluídos se a lista de canais habilitados não estiver vazia
                if self.config["enabled_channels"] and chan_id not in self.config["enabled_channels"]:
                    continue
                
                # Calcular taxas ótimas
                optimal_fees = self.calculate_optimal_fees(chan_id)
                
                # Preparar ponto do canal
                funding_txid = channel["channel_point"].split(":")[0]
                output_index = int(channel["channel_point"].split(":")[1])
                chan_point = {
                    "funding_txid_str": funding_txid,
                    "output_index": output_index
                }
                
                # Atualizar taxas do canal
                update_result = self.lnd_client.update_channel_policy(
                    global_update=False,
                    chan_point=chan_point,
                    base_fee_msat=optimal_fees["base_fee_msat"],
                    fee_rate=optimal_fees["fee_rate"],
                    time_lock_delta=optimal_fees["time_lock_delta"]
                )
                
                if "error" in update_result:
                    logger.error(f"Erro ao atualizar taxas do canal {chan_id}: {update_result['error']}")
                else:
                    logger.info(f"Taxas do canal {chan_id} atualizadas: base_fee={optimal_fees['base_fee_msat']}, rate={optimal_fees['fee_rate']}")
                    
                    # Registrar a atualização no histórico
                    if chan_id in self.channel_stats:
                        timestamp = int(time.time())
                        fee_data = {
                            "timestamp": timestamp,
                            "base_fee_msat": optimal_fees["base_fee_msat"],
                            "fee_rate": optimal_fees["fee_rate"],
                            "time_lock_delta": optimal_fees["time_lock_delta"]
                        }
                        
                        self.channel_stats[chan_id]["fee_history"].append(fee_data)
                        
                        # Limitar o histórico
                        max_history = 24 * 30
                        if len(self.channel_stats[chan_id]["fee_history"]) > max_history:
                            self.channel_stats[chan_id]["fee_history"] = self.channel_stats[chan_id]["fee_history"][-max_history:]
            
            # Salvar estatísticas atualizadas
            self._save_stats()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar taxas dos canais: {e}")
    
    def run_once(self) -> None:
        """Executa uma iteração do gerenciador de taxas"""
        logger.info("Iniciando ciclo de atualização de taxas")
        
        # Coletar dados dos canais
        self.collect_channel_data()
        
        # Atualizar taxas
        self.update_channel_fees()
        
        logger.info("Ciclo de atualização de taxas concluído")
    
    def start(self) -> None:
        """Inicia o gerenciador de taxas em um thread separado"""
        if self.running:
            logger.warning("Gerenciador de taxas já está em execução")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        
        logger.info("Gerenciador de taxas iniciado")
    
    def stop(self) -> None:
        """Para o gerenciador de taxas"""
        if not self.running:
            logger.warning("Gerenciador de taxas não está em execução")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        
        logger.info("Gerenciador de taxas parado")
    
    def _run_loop(self) -> None:
        """Loop principal do gerenciador de taxas"""
        while self.running:
            try:
                self.run_once()
                
                # Esperar pelo próximo ciclo
                interval = self.config["update_interval_seconds"]
                logger.info(f"Aguardando {interval} segundos até o próximo ciclo")
                
                # Verificar a flag running a cada segundo para permitir parada rápida
                for _ in range(interval):
                    if not self.running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"Erro no loop do gerenciador de taxas: {e}")
                # Esperar um pouco antes de tentar novamente
                time.sleep(60)


if __name__ == "__main__":
    # Exemplo de uso
    from lnd_client_rest import LNDClient
    
    # Definir modo de desenvolvimento para simular respostas
    os.environ["LND_DEV_MODE"] = "1"
    
    # Criar cliente LND
    client = LNDClient()
    
    # Criar gerenciador de taxas
    fee_manager = FeeManager(client)
    
    # Executar uma vez
    fee_manager.run_once()
    
    # Ou iniciar em modo contínuo
    # fee_manager.start()
    # try:
    #     # Manter o programa em execução
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     fee_manager.stop()
