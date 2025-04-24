/**
 * Dashboard JavaScript - Versão corrigida para problemas de gráficos
 * Esta versão resolve o problema de crescimento vertical contínuo dos gráficos
 */

// Objeto para armazenar referências aos gráficos
let charts = {};

// Cores para os gráficos
const chartColors = {
    blue: 'rgba(54, 162, 235, 0.7)',
    green: 'rgba(75, 192, 192, 0.7)',
    orange: 'rgba(255, 159, 64, 0.7)',
    red: 'rgba(255, 99, 132, 0.7)',
    purple: 'rgba(153, 102, 255, 0.7)',
    yellow: 'rgba(255, 205, 86, 0.7)',
    grey: 'rgba(201, 203, 207, 0.7)'
};

// Inicialização quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Aplicar estilos fixos aos containers de gráficos
    applyFixedStyles();
    
    // Carregar dados iniciais
    loadDashboardData();
    
    // Configurar botão de atualização manual
    const refreshButton = document.getElementById('refresh-button');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            // Limpar e recriar todos os gráficos
            Object.keys(charts).forEach(id => {
                if (charts[id]) {
                    charts[id].destroy();
                    charts[id] = null;
                }
            });
            charts = {};
            
            // Recarregar dados
            loadDashboardData();
        });
    }
});

/**
 * Aplica estilos fixos aos containers de gráficos
 */
function applyFixedStyles() {
    document.querySelectorAll('.chart-container').forEach(container => {
        container.style.height = '300px';
        container.style.maxHeight = '300px';
        container.style.position = 'relative';
        container.style.width = '100%';
        container.style.overflow = 'hidden';
    });
}

/**
 * Carrega os dados do dashboard da API
 */
function loadDashboardData() {
    // Mostrar indicador de carregamento
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'block';
    }
    
    // Carregar informações do node
    fetch('/api/node/info')
        .then(response => response.json())
        .then(data => {
            updateNodeInfo(data);
        })
        .catch(error => {
            console.error('Erro ao carregar informações do node:', error);
        });
    
    // Carregar canais
    fetch('/api/channels')
        .then(response => response.json())
        .then(data => {
            updateChannelsInfo(data);
            createChannelCharts(data);
        })
        .catch(error => {
            console.error('Erro ao carregar informações dos canais:', error);
        })
        .finally(() => {
            // Esconder indicador de carregamento
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
        });
    
    // Carregar status da automação
    fetch('/api/fees/status')
        .then(response => response.json())
        .then(data => {
            updateAutomationStatus(data);
        })
        .catch(error => {
            console.error('Erro ao carregar status da automação:', error);
        });
}

/**
 * Atualiza as informações do node na interface
 */
function updateNodeInfo(data) {
    const nodeAlias = document.getElementById('node-alias');
    const nodePubkey = document.getElementById('node-pubkey');
    const nodeChannels = document.getElementById('node-channels');
    const nodePendingChannels = document.getElementById('node-pending-channels');
    const nodeBlockHeight = document.getElementById('node-block-height');
    
    if (nodeAlias) nodeAlias.textContent = data.alias || 'N/A';
    if (nodePubkey) nodePubkey.textContent = data.identity_pubkey || 'N/A';
    if (nodeChannels) nodeChannels.textContent = data.num_active_channels || '0';
    if (nodePendingChannels) nodePendingChannels.textContent = data.num_pending_channels || '0';
    if (nodeBlockHeight) nodeBlockHeight.textContent = data.block_height || 'N/A';
}

/**
 * Atualiza as informações dos canais na interface
 */
function updateChannelsInfo(data) {
    const channels = data.channels || [];
    
    // Calcular estatísticas
    let totalCapacity = 0;
    let totalLocalBalance = 0;
    let totalRemoteBalance = 0;
    
    channels.forEach(channel => {
        totalCapacity += parseInt(channel.capacity) || 0;
        totalLocalBalance += parseInt(channel.local_balance) || 0;
        totalRemoteBalance += parseInt(channel.remote_balance) || 0;
    });
    
    // Atualizar estatísticas na interface
    const totalChannelsElement = document.getElementById('total-channels');
    const totalCapacityElement = document.getElementById('total-capacity');
    const totalLocalBalanceElement = document.getElementById('total-local-balance');
    const totalRemoteBalanceElement = document.getElementById('total-remote-balance');
    
    if (totalChannelsElement) totalChannelsElement.textContent = channels.length;
    if (totalCapacityElement) totalCapacityElement.textContent = formatSats(totalCapacity);
    if (totalLocalBalanceElement) totalLocalBalanceElement.textContent = formatSats(totalLocalBalance);
    if (totalRemoteBalanceElement) totalRemoteBalanceElement.textContent = formatSats(totalRemoteBalance);
    
    // Atualizar tabela de canais
    updateChannelsTable(channels);
}

/**
 * Atualiza a tabela de canais
 */
function updateChannelsTable(channels) {
    const tableBody = document.getElementById('channels-table-body');
    if (!tableBody) return;
    
    // Limpar tabela
    tableBody.innerHTML = '';
    
    // Adicionar linhas para cada canal
    channels.forEach(channel => {
        const row = document.createElement('tr');
        
        // Calcular porcentagem de balanço local
        const capacity = parseInt(channel.capacity) || 1;
        const localBalance = parseInt(channel.local_balance) || 0;
        const localPercent = Math.round((localBalance / capacity) * 100);
        
        // Criar células
        row.innerHTML = `
            <td>${channel.remote_pubkey.substring(0, 10)}...</td>
            <td>${formatSats(channel.capacity)}</td>
            <td>
                <div class="progress">
                    <div class="progress-bar" role="progressbar" 
                         style="width: ${localPercent}%;" 
                         aria-valuenow="${localPercent}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                        ${localPercent}%
                    </div>
                </div>
            </td>
            <td>${formatSats(channel.local_balance)}</td>
            <td>${formatSats(channel.remote_balance)}</td>
            <td>${channel.active ? '<span class="badge bg-success">Ativo</span>' : '<span class="badge bg-danger">Inativo</span>'}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

/**
 * Atualiza o status da automação na interface
 */
function updateAutomationStatus(data) {
    const statusElement = document.getElementById('automation-status');
    const lastUpdateElement = document.getElementById('last-update');
    const nextUpdateElement = document.getElementById('next-update');
    
    if (statusElement) {
        statusElement.textContent = data.running ? 'Ativo' : 'Inativo';
        statusElement.className = data.running ? 'text-success' : 'text-danger';
    }
    
    if (lastUpdateElement && data.last_update) {
        lastUpdateElement.textContent = formatDateTime(data.last_update);
    }
    
    if (nextUpdateElement && data.next_update) {
        nextUpdateElement.textContent = formatDateTime(data.next_update);
    }
}

/**
 * Cria os gráficos de canais
 */
function createChannelCharts(data) {
    const channels = data.channels || [];
    
    // Dados para o gráfico de balanço
    const balanceData = {
        labels: ['Balanço Local', 'Balanço Remoto'],
        datasets: [{
            data: [
                channels.reduce((sum, channel) => sum + (parseInt(channel.local_balance) || 0), 0),
                channels.reduce((sum, channel) => sum + (parseInt(channel.remote_balance) || 0), 0)
            ],
            backgroundColor: [chartColors.blue, chartColors.orange],
            borderWidth: 1
        }]
    };
    
    // Criar gráfico de balanço
    createFixedChart('balance-chart', 'doughnut', balanceData);
    
    // Dados para o gráfico de distribuição de canais
    // Agrupar canais por capacidade
    const capacityGroups = {
        'Pequeno (<1M)': 0,
        'Médio (1M-5M)': 0,
        'Grande (>5M)': 0
    };
    
    channels.forEach(channel => {
        const capacity = parseInt(channel.capacity) || 0;
        if (capacity < 1000000) {
            capacityGroups['Pequeno (<1M)']++;
        } else if (capacity < 5000000) {
            capacityGroups['Médio (1M-5M)']++;
        } else {
            capacityGroups['Grande (>5M)']++;
        }
    });
    
    const distributionData = {
        labels: Object.keys(capacityGroups),
        datasets: [{
            label: 'Número de Canais',
            data: Object.values(capacityGroups),
            backgroundColor: [chartColors.green, chartColors.blue, chartColors.purple],
            borderWidth: 1
        }]
    };
    
    // Criar gráfico de distribuição
    createFixedChart('distribution-chart', 'bar', distributionData);
    
    // Simular dados históricos para o gráfico de taxas
    // Em uma aplicação real, estes dados viriam da API
    const feeHistoryData = {
        labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
        datasets: [{
            label: 'Taxa Base Média (msat)',
            data: [1000, 1200, 1100, 1300, 1500, 1400],
            borderColor: chartColors.blue,
            backgroundColor: 'transparent',
            borderWidth: 2,
            tension: 0.4
        }, {
            label: 'Taxa Proporcional Média (ppm)',
            data: [200, 250, 300, 280, 320, 350],
            borderColor: chartColors.green,
            backgroundColor: 'transparent',
            borderWidth: 2,
            tension: 0.4
        }]
    };
    
    // Criar gráfico de histórico de taxas
    createFixedChart('fee-history-chart', 'line', feeHistoryData);
}

/**
 * Cria um gráfico com configurações fixas para evitar o crescimento vertical
 */
function createFixedChart(canvasId, type, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    // Se já existe um gráfico para este canvas, destruí-lo
    if (charts[canvasId]) {
        charts[canvasId].destroy();
        charts[canvasId] = null;
    }
    
    // Configurações específicas para cada tipo de gráfico
    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            }
        },
        animation: {
            duration: 0 // Desativar animações para evitar problemas de renderização
        }
    };
    
    // Adicionar configurações específicas para gráficos de barras e linhas
    if (type === 'bar' || type === 'line') {
        options.scales = {
            y: {
                beginAtZero: true,
                // Definir um limite máximo fixo para evitar o esticamento
                max: type === 'line' ? 2000 : 10
            }
        };
    }
    
    // Criar o gráfico
    charts[canvasId] = new Chart(canvas, {
        type: type,
        data: data,
        options: options
    });
}

/**
 * Formata um valor em satoshis para exibição
 */
function formatSats(sats) {
    return parseInt(sats).toLocaleString() + ' sats';
}

/**
 * Formata uma data/hora para exibição
 */
function formatDateTime(dateTimeStr) {
    const date = new Date(dateTimeStr);
    return date.toLocaleString();
}