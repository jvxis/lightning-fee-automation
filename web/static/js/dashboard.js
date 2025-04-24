/**
 * Dashboard JavaScript - Versão corrigida para problemas de esticamento vertical
 * Esta versão mantém toda a funcionalidade original enquanto resolve o problema dos gráficos
 */

// Variáveis globais
let nodeInfo = {};
let channels = [];
let feeManagerStatus = {};
let charts = {};

// Inicialização quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Aplicar estilos fixos aos containers de gráficos
    applyFixedStyles();
    
    // Inicializar componentes
    initAutomationToggle();
    initUpdateFeesButton();
    
    // Carregar dados
    loadNodeInfo();
    loadChannels();
    loadFeeManagerStatus();
    
    // Atualizar periodicamente
    setInterval(loadNodeInfo, 60000); // A cada minuto
    setInterval(loadChannels, 60000); // A cada minuto
    setInterval(loadFeeManagerStatus, 30000); // A cada 30 segundos
});

/**
 * Aplica estilos fixos aos containers de gráficos
 * Esta função é crucial para evitar o esticamento vertical
 */
function applyFixedStyles() {
    document.querySelectorAll('.chart-container').forEach(container => {
        container.style.height = '300px';
        container.style.maxHeight = '300px';
        container.style.overflow = 'hidden';
        container.style.position = 'relative';
    });
}

/**
 * Inicializa o toggle de automação
 */
function initAutomationToggle() {
    const automationToggle = document.getElementById('automationToggle');
    if (!automationToggle) return;
    
    automationToggle.addEventListener('change', function() {
        const isRunning = this.checked;
        
        // Chamar API para iniciar/parar automação
        const endpoint = isRunning ? '/api/fees/start' : '/api/fees/stop';
        
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(isRunning ? 'Automação iniciada com sucesso!' : 'Automação parada com sucesso!', 'success');
                loadFeeManagerStatus();
            } else {
                showAlert(`Erro: ${data.error}`, 'danger');
                // Reverter o toggle
                automationToggle.checked = !isRunning;
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            showAlert(`Erro ao ${isRunning ? 'iniciar' : 'parar'} automação: ${error}`, 'danger');
            // Reverter o toggle
            automationToggle.checked = !isRunning;
        });
    });
}

/**
 * Inicializa o botão de atualização de taxas
 */
function initUpdateFeesButton() {
    const updateFeesBtn = document.getElementById('updateFeesBtn');
    if (!updateFeesBtn) return;
    
    updateFeesBtn.addEventListener('click', function() {
        // Desabilitar botão durante a atualização
        updateFeesBtn.disabled = true;
        updateFeesBtn.innerHTML = '<i class="bi bi-arrow-repeat me-2"></i>Atualizando...';
        
        // Chamar API para atualizar taxas
        fetch('/api/fees/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Taxas atualizadas com sucesso!', 'success');
                // Recarregar dados
                loadChannels();
            } else {
                showAlert(`Erro: ${data.error}`, 'danger');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            showAlert(`Erro ao atualizar taxas: ${error}`, 'danger');
        })
        .finally(() => {
            // Reabilitar botão
            updateFeesBtn.disabled = false;
            updateFeesBtn.innerHTML = '<i class="bi bi-arrow-repeat me-2"></i>Atualizar Taxas Agora';
        });
    });
}

/**
 * Carrega informações do node
 */
function loadNodeInfo() {
    fetch('/api/node/info')
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                nodeInfo = data;
                updateNodeInfoUI();
            } else {
                console.error('Erro ao carregar informações do node:', data.error);
                const nodeStatus = document.getElementById('nodeStatus');
                if (nodeStatus) {
                    nodeStatus.className = 'badge bg-danger';
                    nodeStatus.textContent = 'Offline';
                }
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            const nodeStatus = document.getElementById('nodeStatus');
            if (nodeStatus) {
                nodeStatus.className = 'badge bg-danger';
                nodeStatus.textContent = 'Erro';
            }
        });
}

/**
 * Atualiza a UI com as informações do node
 */
function updateNodeInfoUI() {
    // Atualizar status do node
    const nodeStatus = document.getElementById('nodeStatus');
    const nodeAlias = document.getElementById('nodeAlias');
    const nodePubkey = document.getElementById('nodePubkey');
    const activeChannels = document.getElementById('activeChannels');
    const activeChannelsCount = document.getElementById('activeChannelsCount');
    const pendingChannelsCount = document.getElementById('pendingChannelsCount');
    
    if (nodeStatus) {
        nodeStatus.className = 'badge bg-success';
        nodeStatus.textContent = 'Online';
    }
    
    // Atualizar alias e pubkey
    if (nodeAlias) nodeAlias.textContent = nodeInfo.alias || 'N/A';
    if (nodePubkey) nodePubkey.textContent = nodeInfo.identity_pubkey || 'N/A';
    
    // Atualizar contagem de canais
    const activeCount = nodeInfo.num_active_channels || 0;
    const pendingCount = nodeInfo.num_pending_channels || 0;
    
    if (activeChannels) activeChannels.textContent = activeCount;
    if (activeChannelsCount) activeChannelsCount.textContent = activeCount;
    if (pendingChannelsCount) pendingChannelsCount.textContent = pendingCount;
}

/**
 * Carrega a lista de canais
 */
function loadChannels() {
    fetch('/api/channels')
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                channels = data.channels || [];
                updateChannelsUI();
                updateChannelsTable();
                updateFeeCharts();
                
                // Reaplicar estilos fixos após atualizar os gráficos
                applyFixedStyles();
            } else {
                console.error('Erro ao carregar canais:', data.error);
            }
        })
        .catch(error => {
            console.error('Erro:', error);
        });
}

/**
 * Atualiza a UI com os dados dos canais
 */
function updateChannelsUI() {
    // Calcular balanço total
    let totalLocalBalance = 0;
    let totalRemoteBalance = 0;
    
    channels.forEach(channel => {
        totalLocalBalance += parseInt(channel.local_balance || 0);
        totalRemoteBalance += parseInt(channel.remote_balance || 0);
    });
    
    // Atualizar UI
    const localBalance = document.getElementById('localBalance');
    const remoteBalance = document.getElementById('remoteBalance');
    
    if (localBalance) localBalance.textContent = formatSats(totalLocalBalance);
    if (remoteBalance) remoteBalance.textContent = formatSats(totalRemoteBalance);
}

/**
 * Atualiza a tabela de canais
 */
function updateChannelsTable() {
    const tableBody = document.getElementById('channelsTableBody');
    if (!tableBody) return;
    
    if (channels.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" class="text-center">Nenhum canal encontrado</td></tr>';
        return;
    }
    
    // Limpar tabela
    tableBody.innerHTML = '';
    
    // Adicionar linhas
    channels.forEach(channel => {
        const capacity = parseInt(channel.capacity || 0);
        const localBalance = parseInt(channel.local_balance || 0);
        const remoteBalance = parseInt(channel.remote_balance || 0);
        const localPercent = capacity > 0 ? (localBalance / capacity * 100).toFixed(1) : 0;
        const remotePercent = capacity > 0 ? (remoteBalance / capacity * 100).toFixed(1) : 0;
        
        // Obter taxas do canal (simulado para demonstração)
        const baseFee = '1000 msat';
        const feeRate = '0.000001 (1 ppm)';
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${shortenString(channel.chan_id)}</td>
            <td>${formatSats(capacity)}</td>
            <td>${formatSats(localBalance)} (${localPercent}%)</td>
            <td>${formatSats(remoteBalance)} (${remotePercent}%)</td>
            <td>
                <div class="progress">
                    <div class="progress-bar bg-primary" role="progressbar" style="width: ${localPercent}%" aria-valuenow="${localPercent}" aria-valuemin="0" aria-valuemax="100"></div>
                    <div class="progress-bar bg-success" role="progressbar" style="width: ${remotePercent}%" aria-valuenow="${remotePercent}" aria-valuemin="0" aria-valuemax="100"></div>
                </div>
            </td>
            <td>${baseFee}</td>
            <td>${feeRate}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

/**
 * Atualiza os gráficos de taxas
 */
function updateFeeCharts() {
    // Criar dados para os gráficos (simulados para demonstração)
    const avgFeesData = {
        labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
        datasets: [
            {
                label: 'Taxa Base Média (msat)',
                data: [1000, 1200, 1100, 1300, 1250, 1400],
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                tension: 0.4
            },
            {
                label: 'Taxa Proporcional Média (ppm)',
                data: [1, 2, 3, 2, 4, 5],
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                tension: 0.4
            }
        ]
    };
    
    const feeDistributionData = {
        labels: ['0-500', '501-1000', '1001-2000', '2001-5000', '5001+'],
        datasets: [
            {
                label: 'Número de Canais',
                data: [2, 5, 3, 1, 0],
                backgroundColor: [
                    'rgba(54, 162, 235, 0.6)',
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(255, 206, 86, 0.6)',
                    'rgba(255, 99, 132, 0.6)',
                    'rgba(153, 102, 255, 0.6)'
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(153, 102, 255, 1)'
                ],
                borderWidth: 1
            }
        ]
    };
    
    // Criar ou atualizar gráficos
    createOrUpdateChart('avgFeesChart', 'line', avgFeesData);
    createOrUpdateChart('feeDistributionChart', 'bar', feeDistributionData);
}

/**
 * Cria ou atualiza um gráfico com configurações otimizadas para evitar esticamento
 */
function createOrUpdateChart(canvasId, type, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    // Se já existe um gráfico para este canvas, destruí-lo
    if (charts[canvasId]) {
        charts[canvasId].destroy();
        delete charts[canvasId];
    }
    
    // Configurações otimizadas para evitar esticamento vertical
    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            }
        },
        animation: {
            duration: 0 // Desativar animações completamente
        }
    };
    
    // Adicionar configurações específicas para gráficos de barras e linhas
    if (type === 'bar' || type === 'line') {
        options.scales = {
            y: {
                beginAtZero: true,
                // Definir um limite máximo fixo (não sugerido) para evitar o esticamento
                max: type === 'line' ? 2000 : 10
            }
        };
    }
    
    // Criar o gráfico
    charts[canvasId] = new Chart(canvas.getContext('2d'), {
        type: type,
        data: data,
        options: options
    });
}

/**
 * Carrega o status do gerenciador de taxas
 */
function loadFeeManagerStatus() {
    fetch('/api/fees/status')
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                feeManagerStatus = data;
                updateFeeManagerStatusUI();
            } else {
                console.error('Erro ao carregar status do gerenciador de taxas:', data.error);
            }
        })
        .catch(error => {
            console.error('Erro:', error);
        });
}

/**
 * Atualiza a UI com o status do gerenciador de taxas
 */
function updateFeeManagerStatusUI() {
    // Atualizar toggle de automação
    const automationToggle = document.getElementById('automationToggle');
    const feeStrategy = document.getElementById('feeStrategy');
    
    if (automationToggle) automationToggle.checked = feeManagerStatus.running;
    
    // Atualizar estratégia
    if (feeStrategy) feeStrategy.textContent = formatStrategy(feeManagerStatus.strategy);
    
    // Atualizar tabela de atualizações recentes (simulado para demonstração)
    updateRecentFeeUpdatesTable();
}

/**
 * Atualiza a tabela de atualizações recentes de taxas
 */
function updateRecentFeeUpdatesTable() {
    const tableBody = document.getElementById('feeUpdatesTableBody');
    if (!tableBody) return;
    
    // Dados simulados para demonstração
    const updates = [
        {
            timestamp: new Date(Date.now() - 3600000).toLocaleString(),
            channel: '724725106597969921',
            oldBaseFee: '1000',
            newBaseFee: '1200',
            oldFeeRate: '0.000001',
            newFeeRate: '0.000002'
        },
        {
            timestamp: new Date(Date.now() - 7200000).toLocaleString(),
            channel: '724725106597969922',
            oldBaseFee: '1500',
            newBaseFee: '1300',
            oldFeeRate: '0.000003',
            newFeeRate: '0.000002'
        }
    ];
    
    if (updates.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhuma atualização de taxa recente</td></tr>';
        return;
    }
    
    // Limpar tabela
    tableBody.innerHTML = '';
    
    // Adicionar linhas
    updates.forEach(update => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${update.timestamp}</td>
            <td>${shortenString(update.channel)}</td>
            <td>${update.oldBaseFee} msat</td>
            <td>${update.newBaseFee} msat</td>
            <td>${formatFeeRate(update.oldFeeRate)}</td>
            <td>${formatFeeRate(update.newFeeRate)}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

/**
 * Formata um valor em satoshis para exibição
 */
function formatSats(sats) {
    return `${parseInt(sats).toLocaleString()} sats`;
}

/**
 * Formata uma taxa proporcional para exibição
 */
function formatFeeRate(rate) {
    const ppm = parseFloat(rate) * 1000000;
    return `${rate} (${ppm} ppm)`;
}

/**
 * Formata o nome da estratégia para exibição
 */
function formatStrategy(strategy) {
    switch (strategy) {
        case 'balanced':
            return 'Balanceada';
        case 'competitive':
            return 'Competitiva';
        case 'profitable':
            return 'Lucrativa';
        default:
            return strategy;
    }
}

/**
 * Encurta uma string para exibição
 */
function shortenString(str, maxLength = 10) {
    if (!str) return '';
    if (str.length <= maxLength) return str;
    return str.substring(0, maxLength) + '...';
}

/**
 * Exibe um alerta na página
 */
function showAlert(message, type = 'info') {
    // Criar elemento de alerta
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Adicionar ao topo da página
    const main = document.querySelector('main');
    if (main) {
        main.insertBefore(alertDiv, main.firstChild);
        
        // Remover após 5 segundos
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}