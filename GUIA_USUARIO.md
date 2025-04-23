# Guia de Instalação e Uso - LND Fee Automation

Este guia fornece instruções detalhadas para instalar, configurar e utilizar a aplicação LND Fee Automation para automatizar as taxas do seu node Lightning Network.

## Índice

1. [Instalação](#instalação)
2. [Configuração Inicial](#configuração-inicial)
3. [Iniciando a Aplicação](#iniciando-a-aplicação)
4. [Usando a Interface Web](#usando-a-interface-web)
5. [Configurando Estratégias de Taxas](#configurando-estratégias-de-taxas)
6. [Monitoramento e Manutenção](#monitoramento-e-manutenção)

## Instalação

### Requisitos do Sistema

- Python 3.8 ou superior
- Node LND ativo e acessível
- Acesso ao arquivo `tls.cert` e `admin.macaroon` do LND

### Passo a Passo

1. **Clone o repositório**

```bash
git clone https://github.com/jvxis/lightning-fee-automation.git
cd lightning-fee-automation
```

2. **Crie um ambiente virtual (recomendado)**

```bash
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. **Instale as dependências**

```bash
pip3 install -r requirements.txt
```

4. **Prepare os arquivos de acesso ao LND**

Você precisará dos arquivos `tls.cert` e `admin.macaroon` do seu node LND. Estes arquivos geralmente estão localizados em:

- Linux: `~/.lnd/`
- macOS: `~/Library/Application Support/Lnd/`
- Windows: `%APPDATA%\Lnd\`

Copie esses arquivos para um local seguro ou anote o caminho completo para configuração posterior.

## Configuração Inicial

1. **Execute o script de configuração**

```bash
python3 create_config.py
```

2. **Siga as instruções interativas**

O script irá solicitar as seguintes informações:

- Host do LND (padrão: localhost)
- Porta do LND (padrão: 8080)
- Caminho para o arquivo tls.cert
- Caminho para o arquivo admin.macaroon
- Estratégia de taxas inicial (balanceada, competitiva ou lucrativa)
- Intervalo de atualização automática (em segundos)

3. **Verifique a configuração**

Após a conclusão, o script criará um arquivo `config.json` no diretório raiz. Você pode editar este arquivo manualmente se necessário.

## Iniciando a Aplicação

1. **Inicie o servidor web**

```bash
cd web
python3 app.py
```

2. **Acesse a interface web**

Abra seu navegador e acesse:

```
http://localhost:5000
```

3. **Verificação inicial**

Na página inicial, você verá o status do seu node e um botão para acessar o dashboard. Verifique se o status mostra "Online", indicando que a conexão com o LND está funcionando corretamente.

## Usando a Interface Web

### Dashboard

O dashboard fornece uma visão geral do seu node e das taxas dos canais:

- **Informações do Node**: Mostra o alias, pubkey e status do seu node
- **Estatísticas de Canais**: Exibe o número de canais ativos e pendentes
- **Liquidez**: Mostra o balanço local e remoto total
- **Estatísticas de Taxas**: Apresenta gráficos de taxas médias e distribuição
- **Balanço dos Canais**: Lista todos os canais com suas informações de balanço e taxas
- **Atualizações Recentes**: Mostra o histórico das últimas atualizações de taxas

### Gerenciamento de Canais

A página de canais permite gerenciar individualmente cada canal:

1. **Acessando a página de canais**

Clique em "Canais" no menu lateral.

2. **Filtrando canais**

Use os filtros no topo da página para encontrar canais específicos:
- **Status**: Filtre por canais ativos ou inativos
- **Balanço**: Filtre por canais balanceados, com mais liquidez local ou remota
- **Automação**: Filtre por canais com automação habilitada ou desabilitada
- **Ordenação**: Ordene por capacidade, balanço ou taxas

3. **Visualizando detalhes de um canal**

Clique no botão de visualização (ícone de olho) para ver detalhes completos de um canal.

4. **Atualizando taxas manualmente**

Clique no botão de edição (ícone de lápis) para abrir o modal de edição de taxas:
- Defina a nova taxa base (em msat)
- Defina a nova taxa proporcional (em decimal, ex: 0.000001 = 1 ppm)
- Defina o novo time lock delta
- Habilite ou desabilite a automação para este canal
- Clique em "Salvar Alterações"

### Configurações

A página de configurações permite personalizar a automação de taxas:

1. **Acessando as configurações**

Clique em "Configurações" no menu lateral.

2. **Configurações gerais**

- **Intervalo de Atualização**: Define o tempo entre atualizações automáticas (mínimo 60 segundos)
- **Estratégia de Taxas**: Escolha entre balanceada, competitiva ou lucrativa

3. **Configurações de taxas**

- **Taxa Base**: Define os limites mínimo e máximo para a taxa base (em msat)
- **Taxa Proporcional**: Define os limites mínimo e máximo para a taxa proporcional (em decimal)
- **Time Lock Delta**: Define o valor padrão para o time lock delta

4. **Configurações do algoritmo**

- **Peso do Fluxo**: Define a importância do fluxo no cálculo das taxas (0-1)
- **Peso dos Peers**: Define a importância das taxas dos peers no cálculo (0-1)
- **Limites de Fluxo**: Define os limiares para considerar alto ou baixo fluxo

5. **Inclusão/exclusão de canais**

- Escolha entre automatizar todos os canais ou apenas canais selecionados
- Adicione ou remova canais específicos das listas de incluídos ou excluídos

6. **Salvando configurações**

Clique em "Salvar Configurações" no topo da página para aplicar as alterações.

## Configurando Estratégias de Taxas

A aplicação oferece três estratégias diferentes para ajustar as taxas dos canais:

### Estratégia Balanceada

A estratégia balanceada considera tanto o fluxo do canal quanto as taxas dos peers para calcular taxas ótimas. É ideal para nodes que desejam um equilíbrio entre receita e competitividade.

**Quando usar**: Esta é a estratégia recomendada para a maioria dos usuários, pois oferece um bom equilíbrio entre atrair tráfego e maximizar receita.

**Como funciona**:
- Para canais com alto fluxo local (>80% da capacidade), as taxas são aumentadas para incentivar pagamentos de saída
- Para canais com baixo fluxo local (<20% da capacidade), as taxas são reduzidas para incentivar pagamentos de entrada
- Para canais com fluxo equilibrado, as taxas são ajustadas com base nas taxas dos peers

### Estratégia Competitiva

A estratégia competitiva define taxas ligeiramente menores que as dos peers para atrair mais tráfego. É ideal para nodes que desejam aumentar o volume de transações.

**Quando usar**: Use esta estratégia quando seu objetivo principal for aumentar o volume de transações e estabelecer seu node como um roteador confiável na rede.

**Como funciona**:
- As taxas base são definidas 10-20% abaixo das taxas dos peers
- As taxas proporcionais são definidas 5-15% abaixo das taxas dos peers
- Os limites mínimos e máximos configurados são sempre respeitados

### Estratégia Lucrativa

A estratégia lucrativa maximiza o lucro com base no histórico de encaminhamento. É ideal para nodes com canais bem estabelecidos e alta demanda.

**Quando usar**: Use esta estratégia quando seu node já tiver canais bem estabelecidos e você quiser maximizar a receita.

**Como funciona**:
- Para canais com alto volume histórico de transações, as taxas são aumentadas para maximizar o lucro
- Para canais com baixo volume histórico, as taxas são reduzidas para atrair mais tráfego
- As taxas são ajustadas dinamicamente com base no sucesso das transações anteriores

## Monitoramento e Manutenção

### Monitoramento Regular

1. **Verificando o status da automação**

O status da automação é exibido no menu lateral da interface web. Você pode:
- Verificar se a automação está ativa (toggle ligado)
- Ver quando foi a última atualização de taxas
- Ver quando será a próxima atualização programada

2. **Monitorando o desempenho dos canais**

No dashboard, você pode monitorar:
- Distribuição de liquidez entre os canais
- Taxas médias aplicadas
- Histórico de atualizações de taxas

### Manutenção

1. **Atualizações manuais**

Você pode forçar uma atualização manual de todas as taxas clicando no botão "Atualizar Taxas Agora" no menu lateral.

2. **Ajustes de configuração**

Revise periodicamente suas configurações para garantir que estão otimizadas para as condições atuais da rede:
- Ajuste os limites de taxas com base nas tendências da rede
- Experimente diferentes estratégias para encontrar a mais eficaz para seu node
- Ajuste os pesos do algoritmo com base nos resultados observados

3. **Backup da configuração**

É recomendável fazer backup regular do arquivo `config.json` para preservar suas configurações personalizadas.

---

Para mais informações e detalhes técnicos, consulte o arquivo README.md completo.

Se você encontrar problemas ou tiver dúvidas, por favor abra uma issue no repositório do GitHub ou entre em contato com o desenvolvedor.

Desenvolvido com ❤️ para a comunidade Lightning Network.
