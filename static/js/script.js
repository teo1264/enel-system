// ============================================================================
// SISTEMA ENEL - JAVASCRIPT CENTRALIZADO
// ============================================================================

// Função utilitária para mostrar loading
function showLoading(elementId, message = 'Processando...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="status info">🔄 ${message}</div>`;
    }
}

// Função utilitária para mostrar resultado
function showResult(elementId, isSuccess, message, details = {}) {
    const element = document.getElementById(elementId);
    if (element) {
        const statusClass = isSuccess ? 'success' : 'error';
        const icon = isSuccess ? '✅' : '❌';
        
        let html = `<div class="status ${statusClass}">`;
        html += `<h3>${icon} ${message}</h3>`;
        
        // Adicionar detalhes se fornecidos
        Object.keys(details).forEach(key => {
            if (details[key] !== undefined && details[key] !== null) {
                html += `<p><strong>${key}:</strong> ${details[key]}</p>`;
            }
        });
        
        html += '</div>';
        element.innerHTML = html;
    }
}

// Função utilitária para fazer requisições AJAX
async function makeRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        const result = await response.json();
        
        return {
            success: response.ok,
            data: result,
            status: response.status
        };
    } catch (error) {
        return {
            success: false,
            error: error.message,
            status: 0
        };
    }
}

// ============================================================================
// FUNÇÕES ESPECÍFICAS DO SISTEMA ENEL
// ============================================================================

// Processar emails ENEL
async function processarEmails() {
    const resultadoDiv = document.getElementById('resultado');
    const diasAtras = document.getElementById('diasAtras')?.value || 1;
    
    showLoading('resultado', 'Processando emails ENEL... Aguarde...');
    
    const result = await makeRequest('/processar-emails-enel', 'POST', {
        dias_atras: parseInt(diasAtras)
    });
    
    if (result.success && result.data.status === 'sucesso') {
        showResult('resultado', true, 'Processamento ENEL Finalizado!', {
            'Emails processados': result.data.emails_processados || 0,
            'PDFs baixados': result.data.pdfs_baixados || 0,
            'PDFs desprotegidos': result.data.pdfs_desprotegidos || 0,
            'Dados extraídos': result.data.dados_extraidos || 0,
            'Planilhas geradas': result.data.planilhas_geradas || 0
        });
    } else {
        const errorMsg = result.data?.erro || result.error || 'Erro desconhecido';
        showResult('resultado', false, 'Erro no processamento', {'Detalhes': errorMsg});
    }
}

// Testar alertas ENEL
async function testarAlertas() {
    const resultadoDiv = document.getElementById('resultado');
    
    showLoading('resultado', 'Testando sistema de alertas... Aguarde...');
    
    const result = await makeRequest('/testar-alertas', 'POST');
    
    if (result.success && result.data.sucesso_geral) {
        showResult('resultado', true, 'Teste Sistema Alertas: SUCESSO!', {
            'Base CCB': result.data.base_ccb ? '✅ OK' : '❌ Erro',
            'Telegram': result.data.telegram ? '✅ OK' : '❌ Erro',
            'Envio teste': result.data.envio_teste ? '✅ OK' : '❌ Erro'
        });
    } else {
        const errorMsg = result.data?.erro || result.error || 'Testes falharam';
        showResult('resultado', false, 'Erro nos testes', {'Detalhes': errorMsg});
    }
}

// Testar consumo alto
async function testarConsumoAlto() {
    const resultadoDiv = document.getElementById('resultado');
    const limite = document.getElementById('limiteConsumo')?.value || 150;
    
    showLoading('resultado', 'Processando alertas de consumo alto... Aguarde...');
    
    const result = await makeRequest('/processar-alertas-consumo', 'POST', {
        limite_percentual: parseInt(limite)
    });
    
    if (result.success && result.data.sucesso) {
        showResult('resultado', true, 'Alertas Consumo Alto: PROCESSADOS!', {
            'Alertas processados': result.data.alertas_processados || 0,
            'Alertas enviados': result.data.alertas_enviados || 0,
            'Limite usado': result.data.limite_usado + '%'
        });
    } else {
        const errorMsg = result.data?.erro || result.error || 'Falha processando alertas';
        showResult('resultado', false, 'Erro nos alertas', {'Detalhes': errorMsg});
    }
}

// Enviar resumo mensal para admins
async function enviarResumoAdmin() {
    const resultadoDiv = document.getElementById('resultado');
    
    showLoading('resultado', 'Enviando resumo mensal... Aguarde...');
    
    const result = await makeRequest('/enviar-resumo-mensal', 'POST');
    
    if (result.success && result.data.sucesso) {
        showResult('resultado', true, 'Resumo Mensal: ENVIADO!', {
            'Admins contactados': `${result.data.admins_contatados}/${result.data.total_admins}`
        });
    } else {
        const errorMsg = result.data?.erro || result.error || 'Falha enviando resumo';
        showResult('resultado', false, 'Erro no envio', {'Detalhes': errorMsg});
    }
}

// ============================================================================
// INICIALIZAÇÃO E EVENTOS
// ============================================================================

// Executar quando DOM carregado
document.addEventListener('DOMContentLoaded', function() {
    console.log('Sistema ENEL - JavaScript carregado');
    
    // Configurar eventos dos formulários
    const processarForm = document.getElementById('processarForm');
    if (processarForm) {
        processarForm.addEventListener('submit', function(e) {
            e.preventDefault();
            processarEmails();
        });
    }
    
    // Auto-hide mensagens de status após 10 segundos
    setTimeout(function() {
        const statusElements = document.querySelectorAll('.status.success');
        statusElements.forEach(function(element) {
            element.style.opacity = '0.7';
        });
    }, 10000);
});

// ============================================================================
// UTILITÁRIOS GERAIS
// ============================================================================

// Formatar números
function formatNumber(num) {
    return new Intl.NumberFormat('pt-BR').format(num);
}

// Formatar moeda
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Copiar texto para clipboard
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            console.log('Texto copiado para clipboard');
        }).catch(err => {
            console.error('Erro copiando texto: ', err);
        });
    }
}

// Scroll suave para elemento
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}