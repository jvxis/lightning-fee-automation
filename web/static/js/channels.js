/**
 * Channels JavaScript
 * Responsável pela funcionalidade da página de canais
 */

// Variáveis globais
let nodeInfo = {};
let channels = [];
let feeManagerStatus = {};
let currentChannelId = null;

// Inicialização quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar componentes
    initAutomationToggle();
    initUpdateFeesButton();
    initFilters();
    
    // Carregar dados
    loadNodeInfo();
    loadChannels();
    loadFeeManagerStatus();
    
    // Inicializar modal de detalhes do canal
    initChannelDetailsModal();
    
    // Atualizar periodicamente
    setInterval(loadNodeInfo, 60000); // A cada minuto
    setInterval(loadChannels, 60000); // A cada minuto
    setInterval(loadFeeManagerStatus, 30000); // A cada 30 segundos
});

/**
 * Inicializa o toggle de automação
 */
function initAutomationToggle() {
    const automationToggle = document.getElementById('automationToggle');
    
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
 * Inicializa os filtros da página de canais
 */
function initFilters() {
    // Filtro de busca
    const channelSearch = document.getElementById('channelSearch');
    channelSearch.addEventListener('input', filterChannels);
    
    // Filtros de seleção
    const statusFilter = document.getElementById('statusFilter');
    const balanceFilter = document.getElementById('balanceFilter');
    const automationFilter = document.getElementById('automationFilter');
    const sortBy = document.getElementById('sortBy');
    
    statusFilter.addEventListener('change', filterChannels);
    balanceFilter.addEventListener('change', filterChannels);
    automationFilter.addEventListener('change', filterChannels);
    sortBy.addEventListener('change', filterChannels);
}

/**
 * Filtra e ordena a lista de canais
 */
function filterChannels() {
    // Obter valores dos filtros
    const searchTerm = document.getElementById('channelSearch').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    const balanceFilter = document.getElementById('balanceFilter').value;
    const automationFilter = document.getElementById('automationFilter').value;
    const sortBy = document.getElementById('sortBy').value;
    
    // Filtrar canais
    let filteredChannels = channels.filter(channel => {
        // Filtro de busca
        const matchesSearch = 
            channel.chan_id.toLowerCase().includes(searchTerm) || 
            channel.remote_pubkey.toLowerCase().includes(searchTerm);
        
        // Filtro de status
        let matchesStatus = true;
        if (statusFilter === 'active') {
            matchesStatus = channel.active;
        } else if (statusFilter === 'inactive') {
            matchesStatus = !channel.active;
        }
        
        // Filtro de balanço
        let matchesBalance = true;
        if (balanceFilter === 'balanced') {
            const localBalance = parseInt(channel.local_balance || 0);
            const remoteBalance = parseInt(channel.remote_balance || 0);
            const total = localBalance + remoteBalance;
            const ratio = total > 0 ? localBalance / total : 0.5;
            matchesBalance = ratio >= 0.4 && ratio <= 0.6; // 40-60% é considerado balanceado
        } else if (balanceFilter === 'local_heavy') {
            const localBalance = parseInt(channel.local_balance || 0);
            const remoteBalance = parseInt(channel.remote_balance || 0);
            const total = localBalance + remoteBalance;
            const ratio = total > 0 ? localBalance / total : 0.5;
            matchesBalance = ratio > 0.6; // Mais de 60% local
        } else if (balanceFilter === 'remote_heavy') {
            const localBalance = parseInt(channel.local_balance || 0);
            const remoteBalance = parseInt(channel.remote_balance || 0);
            const total = localBalance + remoteBalance;
            const ratio = total > 0 ? localBalance / total : 0.5;
            matchesBalance = ratio < 0.4; // Menos de 40% local
        }
        
        // Filtro de automação (simulado para demonstração)
        let matchesAutomation = true;
        if (automationFilter === 'enabled') {
            // Simulado: canais com ID par são considerados habilitados
            matchesAutomation = parseInt(channel.chan_id) % 2 === 0;
        } else if (automationFilter === 'disabled') {
            // Simulado: canais com ID ímpar são considerados desabilitados
            matchesAutomation = parseInt(channel.chan_id) % 2 !== 0;
        }
        
        return matchesSearch && matchesStatus && matchesBalance && matchesAutomation;
    });
    
    // Ordenar canais
    filteredChannels.sort((a, b) => {
        switch (sortBy) {
            case 'capacity':
                return parseInt(b.capacity || 0) - parseInt(a.capacity || 0);
            case 'local_balance':
                return parseInt(b.local_balance || 0) - parseInt(a.local_balance || 0);
            case 'remote_balance':
                return parseInt(b.remote_balance || 0) - parseInt(a.remote_balance || 0);
            case 'base_fee':
                // Simulado: usar o último dígito do ID como taxa base
                return (parseInt(b.chan_id.slice(-1)) || 0) - (parseInt(a.chan_id.slice(-1)) || 0);
            case 'fee_rate':
                // Simulado: usar o último dígito do ID como taxa proporcional
                return (parseInt(b.chan_id.slice(-1)) || 0) - (parseInt(a.chan_id.slice(-1)) || 0);
            default:
                return 0;
        }
    });
    
    // Atualizar tabela
    updateChannelsListTable(filteredChannels);
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
                document.getElementById('nodeStatus').className = 'badge bg-danger';
                document.getElementById('nodeStatus').textContent = 'Offline';
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            document.getElementById('nodeStatus').className = 'badge bg-danger';
            document.getElementById('nodeStatus').textContent = 'Erro';
        });
}

/**
 * Atualiza a UI com as informações do node
 */
function updateNodeInfoUI() {
    // Atualizar status do node
    document.getElementById('nodeStatus').className = 'badge bg-success';
    document.getElementById('nodeStatus').textContent = 'Online';
    
    // Atualizar contagem de canais ativos
    const activeChannelsCount = nodeInfo.num_active_channels || 0;
    document.getElementById('activeChannels').textContent = activeChannelsCount;
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
                filterChannels(); // Isso irá aplicar os filtros e atualizar a tabela
            } else {
                console.error('Erro ao carregar canais:', data.error);
                document.getElementById('channelsListTableBody').innerHTML = 
                    '<tr><td colspan="9" class="text-center">Erro ao carregar canais: ' + data.error + '</td></tr>';
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            document.getElementById('channelsListTableBody').innerHTML = 
                '<tr><td colspan="9" class="text-center">Erro ao carregar canais: ' + error + '</td></tr>';
        });
}

/**
 * Atualiza a tabela de canais
 */
function updateChannelsListTable(filteredChannels) {
    const tableBody = document.getElementById('channelsListTableBody');
    
    if (filteredChannels.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="9" class="text-center">Nenhum canal encontrado com os filtros atuais</td></tr>';
        return;
    }
    
    // Limpar tabela
    tableBody.innerHTML = '';
    
    // Adicionar linhas
    filteredChannels.forEach(channel => {
        const capacity = parseInt(channel.capacity || 0);
        const localBalance = parseInt(channel.local_balance || 0);
        const remoteBalance = parseInt(channel.remote_balance || 0);
        const localPercent = capacity > 0 ? (localBalance / capacity * 100).toFixed(1) : 0;
        
        // Simular taxas para demonstração
        const baseFee = '1000 msat';
        const feeRate = '0.000001 (1 ppm)';
        
        // Simular status de automação para demonstração
        const isAutomated = parseInt(channel.chan_id) % 2 === 0;
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${channel.chan_id}</td>
            <td>${shortenString(channel.remote_pubkey, 15)}</td>
            <td>${formatSats(capacity)}</td>
            <td>${formatSats(localBalance)}</td>
            <td>${formatSats(remoteBalance)}</td>
            <td>${baseFee}</td>
            <td>${feeRate}</td>
            <td>
                <span class="badge ${isAutomated ? 'bg-success' : 'bg-secondary'}">
                    ${isAutomated ? 'Habilitada' : 'Desabilitada'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-primary view-channel" data-chan-id="${channel.chan_id}">
                    <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-sm btn-warning edit-channel" data-chan-id="${channel.chan_id}">
                    <i class="bi bi-pencil"></i>
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Adicionar event listeners para os botões
    document.querySelectorAll('.view-channel, .edit-channel').forEach(button => {
        button.addEventListener('click', function() {
            const chanId = this.getAttribute('data-chan-id');
            openChannelDetailsModal(chanId);
        });
    });
}

/**
 * Inicializa o modal de detalhes do canal
 */
function initChannelDetailsModal() {
    // Botão de salvar alterações
    document.getElementById('saveChannelFeeChanges').addEventListener('click', function() {
        saveChannelFeeChanges();
    });
}

/**
 * Abre o modal de detalhes do canal
 */
function openChannelDetailsModal(chanId) {
    currentChannelId = chanId;
    
    // Encontrar o canal na lista
    const channel = channels.find(c => c.chan_id === chanId);
    
    if (!channel) {
        showAlert(`Canal ${chanId} não encontrado`, 'danger');
        return;
    }
    
    // Preencher informações básicas do canal
    document.getElementById('modalChanId').textContent = channel.chan_id;
    document.getElementById('modalChanPoint').textContent = channel.channel_point;
    document.getElementById('modalPeer').textContent = shortenString(channel.remote_pubkey, 20);
    document.getElementById('modalCapacity').textContent = formatSats(channel.capacity);
    document.getElementById('modalStatus').textContent = channel.active ? 'Ativo' : 'Inativo';
    
    // Preencher informações de balanço
    const capacity = parseInt(channel.capacity || 0);
    const localBalance = parseInt(channel.local_balance || 0);
    const remoteBalance = parseInt(channel.remote_balance || 0);
    const localPercent = capacity > 0 ? (localBalance / capacity * 100).toFixed(1) : 0;
    const remotePercent = capacity > 0 ? (remoteBalance / capacity * 100).toFixed(1) : 0;
    
    document.getElementById('modalLocalBalance').textContent = formatSats(localBalance);
    document.getElementById('modalRemoteBalance').textContent = formatSats(remoteBalance);
    document.getElementById('modalTotalSent').textContent = formatSats(channel.total_satoshis_sent || 0);
    document.getElementById('modalTotalReceived').textContent = formatSats(channel.total_satoshis_received || 0);
    
    // Atualizar barras de progresso
    document.getElementById('modalLocalBalanceBar').style.width = `${localPercent}%`;
    document.getElementById('modalLocalBalanceBar').textContent = `Local (${localPercent}%)`;
    document.getElementById('modalRemoteBalanceBar').style.width = `${remotePercent}%`;
    document.getElementById('modalRemoteBalanceBar').textContent = `Remoto (${remotePercent}%)`;
    
    // Simular taxas para demonstração
    document.getElementById('modalBaseFee').textContent = '1000 msat';
    document.getElementById('modalFeeRate').textContent = '0.000001 (1 ppm)';
    document.getElementById('modalTimeLockDelta').textContent = '40';
    document.getElementById('modalMinHtlc').textContent = '1000 msat';
    document.getElementById('modalMaxHtlc').textContent = `${parseInt(capacity) * 0.99} msat`;
    
    // Preencher formulário de atualização
    document.getElementById('newBaseFee').value = 1000;
    document.getElementById('newFeeRate').value = 0.000001;
    document.getElementById('newTimeLockDelta').value = 40;
    
    // Simular status de automação para demonstração
    document.getElementById('channelAutomationToggle').checked = parseInt(channel.chan_id) % 2 === 0;
    
    // Abrir modal
    const modal = new bootstrap.Modal(document.getElementById('channelDetailsModal'));
    modal.show();
}

/**
 * Salva as alterações de taxas do canal
 */
function saveChannelFeeChanges() {
    if (!currentChannelId) {
        showAlert('Nenhum canal selecionado', 'danger');
        return;
    }
    
    // Obter valores do formulário
    const baseFee = parseInt(document.getElementById('newBaseFee').value);
    const feeRate = parseFloat(document.getElementById('newFeeRate').value);
    const timeLockDelta = parseInt(document.getElementById('newTimeLockDelta').value);
    const automationEnabled = document.getElementById('channelAutomationToggle').checked;
    
    // Validar valores
    if (isNaN(baseFee) || isNaN(feeRate) || isNaN(timeLockDelta)) {
        showAlert('Valores inválidos', 'danger');
        return;
    }
    
    // Preparar dados para envio
    const data = {
        base_fee_msat: baseFee,
        fee_rate: feeRate,
        time_lock_delta: timeLockDelta
    };
    
    // Chamar API para atualizar taxas
    fetch(`/api/channel/${currentChannelId}/fees`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (!data.error) {
            showAlert('Taxas atualizadas com sucesso!', 'success');
            
            // Atualizar status de automação (simulado para demonstração)
            showAlert(`Automação ${automationEnabled ? 'habilitada' : 'desabilitada'} para o canal ${currentChannelId}`, 'success');
            
            // Fechar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('channelDetailsModal'));
            modal.hide();
            
            // Recarregar dados
            loadChannels();
        } else {
            showAlert(`Erro: ${data.error}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showAlert(`Erro ao atualizar taxas: ${error}`, 'danger');
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
    document.getElementById('automationToggle').checked = feeManagerStatus.running;
}

/**
 * Formata um valor em satoshis para exibição
 */
function formatSats(sats) {
    return `${parseInt(sats).toLocaleString()} sats`;
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
    main.insertBefore(alertDiv, main.firstChild);
    
    // Remover após 5 segundos
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}
