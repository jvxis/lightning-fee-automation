# LND Fee Automation
> **Nota importante**: Esta versão da aplicação usa exclusivamente a API REST do LND, 
> eliminando a necessidade de dependências gRPC que podem ser difíceis de compilar em alguns sistemas.
> A API REST oferece todas as funcionalidades necessárias para a automação de taxas e é muito mais fácil de configurar.
 - Documentação

## Visão Geral

O LND Fee Automation é uma aplicação para automatizar as taxas do seu node Lightning Network (LND) com base no fluxo de entrada e saída de cada canal e nas taxas dos peers. A aplicação permite ajustar automaticamente as taxas para maximizar a receita e manter a competitividade na rede.

## Índice

1. [Requisitos](#requisitos)
2. [Instalação](#instalação)
3. [Configuração](#configuração)
4. [Uso da Interface Web](#uso-da-interface-web)
5. [Estratégias de Taxas](#estratégias-de-taxas)
6. [API REST](#api-rest)
7. [Solução de Problemas](#solução-de-problemas)
8. [Desenvolvimento e Contribuições](#desenvolvimento-e-contribuições)

## Requisitos

- Python 3.8 ou superior
- Acesso à API REST do LND (geralmente na porta 8080)
- Node LND ativo e acessível
- Acesso ao arquivo `tls.cert` e `admin.macaroon` do LND
- Conexão com a internet para a interface web

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/jvxis/lightning-fee-automation.git
cd lightning-fee-automation
```

### 2. Instale as dependências

```bash
pip3 install -r requirements.txt
```

### 3. Configure o acesso ao LND

Copie os arquivos `tls.cert` e `admin.macaroon` do seu node LND para o diretório `~/.lnd/` ou especifique o caminho no arquivo de configuração.

### 4. Execute o script de configuração inicial

```bash
python3 create_config.py
```

Este script irá guiá-lo através da configuração inicial da aplicação, incluindo a conexão com o LND e as estratégias de taxas.

### 5. Inicie a aplicação

```bash
cd web
python3 app.py
```

A aplicação estará disponível em `http://localhost:5000`.

## Configuração

### Arquivo de Configuração

O arquivo de configuração principal é `config.json`, localizado no diretório raiz da aplicação. Ele contém as seguintes configurações:

```json
{
  "lnd_host": "localhost",
  "lnd_port": 8080,
  "lnd_cert_path": "~/.lnd/tls.cert",
  "lnd_macaroon_path": "~/.lnd/admin.macaroon",
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
```

### Parâmetros de Configuração

| Parâmetro | Descrição | Valor Padrão |
|-----------|-----------|--------------|
| `lnd_host` | Host do LND | localhost |
| `lnd_port` | Porta do LND | 8080 |
| `lnd_cert_path` | Caminho para o certificado TLS | ~/.lnd/tls.cert |
| `lnd_macaroon_path` | Caminho para o macaroon de admin | ~/.lnd/admin.macaroon |
| `fee_strategy` | Estratégia de taxas (balanced, competitive, profitable) | balanced |
| `update_interval_seconds` | Intervalo entre atualizações automáticas (segundos) | 3600 |
| `min_base_fee_msat` | Taxa base mínima (msat) | 1000 |
| `max_base_fee_msat` | Taxa base máxima (msat) | 5000 |
| `min_fee_rate` | Taxa proporcional mínima (decimal) | 0.000001 (1 ppm) |
| `max_fee_rate` | Taxa proporcional máxima (decimal) | 0.001 (1000 ppm) |
| `time_lock_delta` | Time lock delta para os canais | 40 |
| `flow_weight` | Peso do fluxo no cálculo das taxas (0-1) | 0.7 |
| `peer_weight` | Peso das taxas dos peers no cálculo (0-1) | 0.3 |
| `high_flow_threshold` | Percentual de capacidade considerado alto fluxo (0-1) | 0.8 |
| `low_flow_threshold` | Percentual de capacidade considerado baixo fluxo (0-1) | 0.2 |
| `excluded_channels` | Lista de IDs de canais excluídos da automação | [] |
| `enabled_channels` | Lista de IDs de canais habilitados para automação (vazio = todos) | [] |

## Uso da Interface Web

A interface web fornece uma maneira fácil de gerenciar e monitorar a automação de taxas do seu node Lightning. Ela está disponível em `http://localhost:5000` após iniciar a aplicação.

### Dashboard

O dashboard fornece uma visão geral do seu node e das taxas dos canais:

- **Informações do Node**: Alias, pubkey e status do node
- **Estatísticas de Canais**: Número de canais ativos e pendentes
- **Liquidez**: Balanço local e remoto total
- **Estatísticas de Taxas**: Gráficos de taxas médias e distribuição de taxas
- **Balanço dos Canais**: Tabela com informações detalhadas sobre cada canal
- **Atualizações Recentes**: Histórico das últimas atualizações de taxas

### Canais

A página de canais permite gerenciar individualmente cada canal:

- **Filtros**: Filtrar canais por status, balanço e automação
- **Lista de Canais**: Visualizar todos os canais com suas informações
- **Detalhes do Canal**: Ver informações detalhadas de um canal específico
- **Atualização Manual**: Atualizar manualmente as taxas de um canal específico
- **Automação por Canal**: Habilitar ou desabilitar a automação para canais específicos

### Configurações

A página de configurações permite personalizar a automação de taxas:

- **Configurações Gerais**: Intervalo de atualização e estratégia de taxas
- **Configurações de Taxas**: Limites de taxas base e proporcionais
- **Configurações do Algoritmo**: Pesos e limiares para o cálculo das taxas
- **Inclusão/Exclusão de Canais**: Gerenciar quais canais são automatizados

## Estratégias de Taxas

A aplicação oferece três estratégias diferentes para ajustar as taxas dos canais:

### Balanceada

A estratégia balanceada considera tanto o fluxo do canal quanto as taxas dos peers para calcular taxas ótimas. Ela é ideal para nodes que desejam um equilíbrio entre receita e competitividade.

- **Alto Fluxo Local (>80%)**: Taxas mais altas para incentivar pagamentos de saída
- **Baixo Fluxo Local (<20%)**: Taxas mais baixas para incentivar pagamentos de entrada
- **Fluxo Equilibrado**: Taxas médias, ajustadas com base nas taxas dos peers

### Competitiva

A estratégia competitiva define taxas ligeiramente menores que as dos peers para atrair mais tráfego. Ela é ideal para nodes que desejam aumentar o volume de transações.

- Taxas base: 10-20% menores que as dos peers
- Taxas proporcionais: 5-15% menores que as dos peers
- Limites mínimos e máximos são respeitados

### Lucrativa

A estratégia lucrativa maximiza o lucro com base no histórico de encaminhamento. Ela é ideal para nodes com canais bem estabelecidos e alta demanda.

- Canais com alto volume histórico: Taxas mais altas
- Canais com baixo volume histórico: Taxas mais baixas para atrair tráfego
- Ajustes dinâmicos com base no sucesso das transações

## API REST

A aplicação fornece uma API REST para integração com outros sistemas:

### Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/node/info` | GET | Obter informações do node |
| `/api/channels` | GET | Listar todos os canais |
| `/api/channel/{chan_id}` | GET | Obter informações de um canal específico |
| `/api/channel/{chan_id}/fees` | POST | Atualizar taxas de um canal específico |
| `/api/fees/status` | GET | Obter status do gerenciador de taxas |
| `/api/fees/update` | POST | Atualizar taxas de todos os canais |
| `/api/fees/start` | POST | Iniciar automação de taxas |
| `/api/fees/stop` | POST | Parar automação de taxas |
| `/api/config` | GET | Obter configuração atual |
| `/api/config` | POST | Atualizar configuração |

### Exemplos de Uso

#### Obter informações do node

```bash
curl http://localhost:5000/api/node/info
```

#### Atualizar taxas de um canal específico

```bash
curl -X POST http://localhost:5000/api/channel/123456789/fees \
  -H "Content-Type: application/json" \
  -d '{"base_fee_msat": 1500, "fee_rate": 0.000002, "time_lock_delta": 40}'
```

#### Iniciar automação de taxas

```bash
curl -X POST http://localhost:5000/api/fees/start
```

## Solução de Problemas

### Problemas de Conexão com o LND

Se você estiver tendo problemas para conectar ao LND:

1. Verifique se o LND está em execução e acessível
2. Verifique se os caminhos para `tls.cert` e `admin.macaroon` estão corretos
3. Verifique se o host e a porta do LND estão corretos
4. Verifique se o macaroon tem permissões suficientes (admin)

### Erros na Atualização de Taxas

Se as taxas não estiverem sendo atualizadas corretamente:

1. Verifique os logs da aplicação para erros específicos
2. Verifique se os canais estão ativos
3. Verifique se os limites de taxas estão configurados corretamente
4. Tente atualizar manualmente as taxas para verificar se há problemas com a API do LND

### Problemas com a Interface Web

Se a interface web não estiver funcionando corretamente:

1. Verifique se a aplicação está em execução
2. Limpe o cache do navegador
3. Verifique os logs do console do navegador para erros JavaScript
4. Tente acessar a API diretamente para verificar se o backend está funcionando

## Desenvolvimento e Contribuições

### Estrutura do Projeto

```
lightning-fee-automation/
├── lnd_client.py         # Cliente para interagir com a API do LND
├── fee_manager.py        # Gerenciador de taxas e algoritmos
├── create_config.py      # Script de configuração inicial
├── config.json           # Arquivo de configuração
├── web/                  # Interface web
│   ├── app.py            # Aplicação Flask
│   ├── templates/        # Templates HTML
│   └── static/           # Arquivos estáticos (CSS, JS)
└── tests/                # Testes unitários e de integração
```

### Executando os Testes

```bash
cd tests
python3 run_tests.py
```

### Contribuindo

Contribuições são bem-vindas! Por favor, siga estas etapas:

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Faça commit das suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um novo Pull Request

---

## Suporte

Se você encontrar problemas ou tiver dúvidas, por favor abra uma issue no repositório do GitHub ou entre em contato com o desenvolvedor.

---

Desenvolvido com ❤️ para a comunidade Lightning Network.
