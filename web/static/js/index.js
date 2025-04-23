/**
 * Index JavaScript
 * Responsável pela funcionalidade da página inicial
 */

// Variáveis globais
let nodeInfo = {};

// Inicialização quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Carregar dados
    loadNodeInfo();
    
    // Atualizar periodicamente
    setInterval(loadNodeInfo, 60000); // A cada minuto
});

/**
 * Carrega informações do node
 */
function loadNodeInfo() {
    fetch('/api/node/info')
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                nodeInfo = data;
                updateNodeStatusContainer();
            } else {
                console.error('Erro ao carregar informações do node:', data.error);
                document.getElementById('nodeStatusContainer').innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        Erro ao conectar com o node: ${data.error}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            document.getElementById('nodeStatusContainer').innerHTML = `
                <div class="alert alert-danger" role="alert">
                    Erro ao conectar com o node: ${error}
                </div>
            `;
        });
}

/**
 * Atualiza o container de status do node
 */
function updateNodeStatusContainer() {
    const container = document.getElementById('nodeStatusContainer');
    
    // Criar conteúdo HTML
    const html = `
        <div class="row">
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-body">
                        <h6 class="card-title">Informações do Node</h6>
                        <table class="table table-sm">
                            <tr>
                                <th>Alias</th>
                                <td>${nodeInfo.alias || 'N/A'}</td>
                            </tr>
                            <tr>
                                <th>Pubkey</th>
                                <td class="text-truncate">${nodeInfo.identity_pubkey || 'N/A'}</td>
                            </tr>
                            <tr>
                                <th>Versão</th>
                                <td>${nodeInfo.version || 'N/A'}</td>
                            </tr>
                            <tr>
                                <th>Status</th>
                                <td>
                                    <span class="badge bg-success">Online</span>
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-body">
                        <h6 class="card-title">Estatísticas</h6>
                        <table class="table table-sm">
                            <tr>
                                <th>Canais Ativos</th>
                                <td>${nodeInfo.num_active_channels || 0}</td>
                            </tr>
                            <tr>
                                <th>Canais Pendentes</th>
                                <td>${nodeInfo.num_pending_channels || 0}</td>
                            </tr>
                            <tr>
                                <th>Peers</th>
                                <td>${nodeInfo.num_peers || 0}</td>
                            </tr>
                            <tr>
                                <th>Altura do Bloco</th>
                                <td>${nodeInfo.block_height || 0}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        <div class="text-center mt-3">
            <a href="/dashboard" class="btn btn-primary">Ir para o Dashboard</a>
        </div>
    `;
    
    // Atualizar container
    container.innerHTML = html;
}
