/**
 * Settings JavaScript
 * Responsável pela funcionalidade da página de configurações
 */

// Variáveis globais
let nodeInfo = {};
let channels = [];
let config = {};
let feeManagerStatus = {};

// Inicialização quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar componentes
    initAutomationToggle();
    initUpdateFeesButton();
    initSaveSettingsButton();
    initChannelSelectionButtons();
    initChannelModeRadios();
    
    // Carregar dados
    loadNodeInfo();
    loadChannels();
    loadConfig();
    loadFeeManagerStatus();
    
    // Atualizar periodicamente
    setInterval(loadNodeInfo, 60000); // A cada minuto
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
 * Inicializa o botão de salvar configurações
 */
function initSaveSettingsButton() {
    const saveSettingsBtn = document.getElementById('saveSettingsBtn');
    
    saveSettingsBtn.addEventListener('click', function() {
        saveSettings();
    });
}

/**
 * Inicializa os botões de seleção de canais
 */
function initChannelSelectionButtons() {
    const addToIncludedBtn = document.getElementById('addToIncluded');
    const addToExcludedBtn = document.getElementById('addToExcluded');
    
    addToIncludedBtn.addEventListener('click', function() {
        moveSelectedChannels('excludedChannels', 'enabledChannels');
    });
    
    addToExcludedBtn.addEventListener('click', function() {
        moveSelectedChannels('enabledChannels', 'excludedChannels');
    });
}

/**
 * Move canais selecionados de uma lista para outra
 */
function moveSelectedChannels(sourceId, targetId) {
    const sourceSelect = document.getElementById(sourceId);
    const targetSelect = document.getElementById(targetId);
    
    // Obter opções selecionadas
    const selectedOptions = Array.from(sourceSelect.selectedOptions);
    
    // Mover cada opção selecionada
    selectedOptions.forEach(option => {
        const newOption = document.createElement('option');
        newOption.value = option.value;
        newOption.text = option.text;
        targetSelect.add(newOption);
        sourceSelect.remove(sourceSelect.options.indexOf(option));
    });
}

/**
 * Inicializa os radios de modo de canal
 */
function initChannelModeRadios() {
    const allChannelsMode = document.getElementById('allChannelsMode');
    const selectiveChannelsMode = document.getElementById('selectiveChannelsMode');
    
    allChannelsMode.addEventListener('change', function() {
        if (this.checked) {
            // Desabilitar lista de canais incluídos
            document.getElementById('enabledChannels').disabled = true;
        }
    });
    
    selectiveChannelsMode.addEventListener('change', function() {
        if (this.checked) {
            // Habilitar lista de canais incluídos
            document.getElementById('enabledChannels').disabled = false;
        }
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
                updateChannelLists();
            } else {
                console.error('Erro ao carregar canais:', data.error);
            }
        })
        .catch(error => {
            console.error('Erro:', error);
        });
}

/**
 * Atualiza as listas de canais incluídos e excluídos
 */
function updateChannelLists() {
    const enabledChannels = document.getElementById('enabledChannels');
    const excludedChannels = document.getElementById('excludedChannels');
    
    // Limpar listas
    enabledChannels.innerHTML = '';
    excludedChannels.innerHTML = '';
    
    // Preencher listas com base na configuração atual
    channels.forEach(channel => {
        const option = document.createElement('option');
        option.value = channel.chan_id;
        option.text = `${channel.chan_id} - ${formatSats(channel.capacity)}`;
        
        // Verificar se o canal está na lista de excluídos
        if (config.excluded_channels && config.excluded_channels.includes(channel.chan_id)) {
            excludedChannels.add(option);
        } 
        // Verificar se o canal está na lista de habilitados
        else if (config.enabled_channels && config.enabled_channels.includes(channel.chan_id)) {
            enabledChannels.add(option);
        }
        // Se não estiver em nenhuma lista e o modo for seletivo, adicionar à lista de excluídos
        else if (config.enabled_channels && config.enabled_channels.length > 0) {
            excludedChannels.add(option);
        }
        // Se não estiver em nenhuma lista e o modo for todos, adicionar à lista de habilitados
        else {
            enabledChannels.add(option);
        }
    });
    
    // Definir estado dos radios
    const allChannelsMode = document.getElementById('allChannelsMode');
    const selectiveChannelsMode = document.getElementById('selectiveChannelsMode');
    
    if (config.enabled_channels && config.enabled_channels.length > 0) {
        selectiveChannelsMode.checked = true;
        enabledChannels.disabled = false;
    } else {
        allChannelsMode.checked = true;
        enabledChannels.disabled = true;
    }
}

/**
 * Carrega a configuração atual
 */
function loadConfig() {
    fetch('/api/config')
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                config = data;
                updateConfigUI();
            } else {
                console.error('Erro ao carregar configuração:', data.error);
                showAlert(`Erro ao carregar configuração: ${data.error}`, 'danger');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            showAlert(`Erro ao carregar configuração: ${error}`, 'danger');
        });
}

/**
 * Atualiza a UI com a configuração atual
 */
function updateConfigUI() {
    // Configurações gerais
    document.getElementById('updateInterval').value = config.update_interval_seconds || 3600;
    document.getElementById('feeStrategy').value = config.fee_strategy || 'balanced';
    
    // Configurações de taxas
    document.getElementById('minBaseFee').value = config.min_base_fee_msat || 1000;
    document.getElementById('maxBaseFee').value = config.max_base_fee_msat || 5000;
    document.getElementById('minFeeRate').value = config.min_fee_rate || 0.000001;
    document.getElementById('maxFeeRate').value = config.max_fee_rate || 0.001;
    document.getElementById('timeLockDelta').value = config.time_lock_delta || 40;
    
    // Configurações do algoritmo
    document.getElementById('flowWeight').value = config.flow_weight || 0.7;
    document.getElementById('peerWeight').value = config.peer_weight || 0.3;
    document.getElementById('highFlowThreshold').value = config.high_flow_threshold || 0.8;
    document.getElementById('lowFlowThreshold').value = config.low_flow_threshold || 0.2;
}

/**
 * Salva as configurações
 */
function saveSettings() {
    // Obter valores dos formulários
    const newConfig = {
        // Configurações gerais
        update_interval_seconds: parseInt(document.getElementById('updateInterval').value),
        fee_strategy: document.getElementById('feeStrategy').value,
        
        // Configurações de taxas
        min_base_fee_msat: parseInt(document.getElementById('minBaseFee').value),
        max_base_fee_msat: parseInt(document.getElementById('maxBaseFee').value),
        min_fee_rate: parseFloat(document.getElementById('minFeeRate').value),
        max_fee_rate: parseFloat(document.getElementById('maxFeeRate').value),
        time_lock_delta: parseInt(document.getElementById('timeLockDelta').value),
        
        // Configurações do algoritmo
        flow_weight: parseFloat(document.getElementById('flowWeight').value),
        peer_weight: parseFloat(document.getElementById('peerWeight').value),
        high_flow_threshold: parseFloat(document.getElementById('highFlowThreshold').value),
        low_flow_threshold: parseFloat(document.getElementById('lowFlowThreshold').value)
    };
    
    // Obter canais habilitados e excluídos
    const allChannelsMode = document.getElementById('allChannelsMode').checked;
    const enabledChannelsSelect = document.getElementById('enabledChannels');
    const excludedChannelsSelect = document.getElementById('excludedChannels');
    
    if (allChannelsMode) {
        // Modo "todos os canais"
        newConfig.enabled_channels = [];
    } else {
        // Modo "canais selecionados"
        newConfig.enabled_channels = Array.from(enabledChannelsSelect.options).map(option => option.value);
    }
    
    // Canais excluídos
    newConfig.excluded_channels = Array.from(excludedChannelsSelect.options).map(option => option.value);
    
    // Validar configuração
    if (newConfig.update_interval_seconds < 60) {
        showAlert('O intervalo de atualização deve ser de pelo menos 60 segundos', 'warning');
        return;
    }
    
    if (newConfig.min_base_fee_msat > newConfig.max_base_fee_msat) {
        showAlert('A taxa base mínima não pode ser maior que a máxima', 'warning');
        return;
    }
    
    if (newConfig.min_fee_rate > newConfig.max_fee_rate) {
        showAlert('A taxa proporcional mínima não pode ser maior que a máxima', 'warning');
        return;
    }
    
    if (newConfig.flow_weight + newConfig.peer_weight !== 1.0) {
        showAlert('A soma dos pesos do fluxo e dos peers deve ser 1.0', 'warning');
        return;
    }
    
    if (newConfig.low_flow_threshold >= newConfig.high_flow_threshold) {
        showAlert('O limite de fluxo baixo deve ser menor que o limite de fluxo alto', 'warning');
        return;
    }
    
    // Salvar configuração
    fetch('/api/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(newConfig)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Configurações salvas com sucesso!', 'success');
            config = data.config;
        } else {
            showAlert(`Erro: ${data.error}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showAlert(`Erro ao salvar configurações: ${error}`, 'danger');
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
