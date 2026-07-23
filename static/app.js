let currentInterval = null;

document.addEventListener('DOMContentLoaded', () => {
    fetchTemplates();
    fetchServers();
    
    // Auto-refresh telemetría cada 3 segundos
    currentInterval = setInterval(fetchServers, 3000);
});

async function fetchTemplates() {
    try {
        const res = await fetch('/api/templates');
        const json = await res.json();
        if (json.status === 'success') {
            const select = document.getElementById('server-template');
            select.innerHTML = json.data.map(t => `<option value="${t}">${t}</option>`).join('');
        }
    } catch (e) {
        console.error("Error loading templates", e);
    }
}

async function fetchServers() {
    try {
        const res = await fetch('/api/servers');
        const json = await res.json();
        
        if (json.status === 'success') {
            renderServers(json.data);
        } else {
            // Silencioso para no spamear en el auto-refresh, a menos que sea un error grave
            console.error(json.message);
        }
    } catch (e) {
        console.error("Error fetching servers", e);
    }
}

function renderServers(servers) {
    const grid = document.getElementById('servers-grid');
    
    if (servers.length === 0) {
        grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 3rem;">
            No hay servidores desplegados. Usa el botón superior para levantar una instancia.
        </div>`;
        return;
    }
    
    let html = '';
    servers.forEach(s => {
        const name = s.Names;
        let state = s.State; 
        const image = s.Image;
        const stats = s.Stats;
        const statusStr = s.Status || '';
        
        // Interpretar si salió de forma limpia (0) o falló
        if (state === 'exited') {
            if (statusStr.includes('(0)')) {
                state = 'exited'; // Detenido limpiamente
            } else {
                state = 'error'; // Caída o forzado
            }
        }
        
        let cpu = '0.00%';
        let ram = '0B / 0B';
        
        if (stats) {
            cpu = stats.CPUPerc || '0.00%';
            ram = stats.MemUsage || '0B / 0B';
        }
        
        let stateClass = state === 'running' ? 'running' : state === 'exited' ? 'exited' : state === 'paused' ? 'paused' : state === 'error' ? 'error' : 'unknown';
        
        html += `
            <div class="card">
                <div class="card-header">
                    <div>
                        <div class="server-title">${name}</div>
                        <div class="server-image">${image}</div>
                    </div>
                    <div class="status-badge ${stateClass}">${state}</div>
                </div>
                
                <div class="stats-container">
                    <div class="stat-item">
                        <div class="label">CPU Usage</div>
                        <div class="value">${cpu}</div>
                    </div>
                    <div class="stat-item">
                        <div class="label">RAM Usage</div>
                        <div class="value">${ram.split(' / ')[0]}</div>
                    </div>
                </div>
                
                <div class="actions">
                    <button class="btn secondary" onclick="viewLogs('${name}')">Logs</button>
                    ${state === 'running' ? `<button class="btn secondary" onclick="doAction('${name}', 'pause')">Pausar</button>` : ''}
                    ${state === 'paused' ? `<button class="btn secondary" onclick="doAction('${name}', 'unpause')">Reanudar</button>` : ''}
                    ${state === 'running' ? `<button class="btn secondary" style="color:var(--warning); border-color:rgba(245, 158, 11, 0.3)" onclick="doAction('${name}', 'stop')">Detener</button>` : ''}
                    ${state !== 'running' && state !== 'paused' ? `<button class="btn secondary" style="color:var(--success); border-color:rgba(16, 185, 129, 0.3)" onclick="doAction('${name}', 'start')">Iniciar</button>` : ''}
                    <button class="btn secondary" style="background: rgba(239, 68, 68, 0.1); color: var(--danger); border:none;" onclick="doAction('${name}', 'destroy')">Borrar</button>
                </div>
            </div>
        `;
    });
    
    grid.innerHTML = html;
}

async function doAction(name, action) {
    if (action === 'destroy' && !confirm(`¿Estás seguro que deseas eliminar el servidor ${name} de forma permanente?`)) return;
    
    // Desactivar temporalmente el refresco para evitar parpadeos visuales
    clearInterval(currentInterval);
    
    try {
        const res = await fetch('/api/action', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, action })
        });
        const json = await res.json();
        
        if (json.status === 'success') {
            showAlert('success', `Acción '${action}' ejecutada correctamente en ${name}.`);
        } else {
            showAlert('error', json.message);
        }
    } catch (e) {
        showAlert('error', 'Fallo de conexión.');
    }
    
    fetchServers();
    currentInterval = setInterval(fetchServers, 3000);
}

async function deployServer() {
    const name = document.getElementById('server-name').value.trim();
    const template = document.getElementById('server-template').value;
    
    if (!name) return showAlert('error', 'Debes ingresar un nombre para el servidor');
    
    closeDeployModal();
    showAlert('success', 'Desplegando servidor... esto tomará unos segundos.');
    
    try {
        const res = await fetch('/api/deploy', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, template })
        });
        const json = await res.json();
        
        if (json.status === 'success') {
            showAlert('success', 'Servidor desplegado exitosamente.');
            document.getElementById('server-name').value = '';
            fetchServers();
        } else {
            showAlert('error', 'Error al desplegar: ' + json.message);
        }
    } catch (e) {
        showAlert('error', 'Fallo de conexión.');
    }
}

let timeoutId;
function showAlert(type, msg) {
    clearTimeout(timeoutId);
    
    const errorAlert = document.getElementById('error-alert');
    const successAlert = document.getElementById('success-alert');
    
    errorAlert.classList.add('hidden');
    successAlert.classList.add('hidden');
    
    const el = type === 'error' ? errorAlert : successAlert;
    el.textContent = msg;
    el.classList.remove('hidden');
    
    timeoutId = setTimeout(() => {
        el.classList.add('hidden');
    }, 5000);
}

function showDeployModal() {
    document.getElementById('deploy-modal').classList.remove('hidden');
}

function closeDeployModal() {
    document.getElementById('deploy-modal').classList.add('hidden');
}

let currentLogServer = null;
let logInterval = null;

async function viewLogs(name) {
    currentLogServer = name;
    document.getElementById('logs-title').textContent = `Logs: ${name}`;
    document.getElementById('logs-container').innerHTML = '<div style="color:var(--text-muted)">Cargando logs...</div>';
    document.getElementById('logs-modal').classList.remove('hidden');
    refreshLogs();
    
    if (logInterval) clearInterval(logInterval);
    logInterval = setInterval(refreshLogs, 3000);
}

function formatLogs(rawText) {
    if (!rawText) return '<div style="color:var(--text-muted)">El servidor no ha generado logs aún.</div>';
    
    // Limpiar códigos ANSI (colores de terminal que ensucian el HTML)
    let text = rawText.replace(/\x1B\[[0-9;]*[a-zA-Z]/g, '');
    
    const lines = text.split('\n');
    let formattedHtml = '';
    
    lines.forEach(line => {
        if (!line.trim()) return;
        
        // Buscar el timestamp inyectado por docker logs -t (cualquier formato ISO que empiece por año-mes-díaT)
        const timeMatch = line.match(/^(\d{4}-\d{2}-\d{2}T\S+)\s+(.*)/);
        let timestamp = '';
        let content = line;
        
        if (timeMatch) {
            try {
                const date = new Date(timeMatch[1]);
                timestamp = `<span class="log-time">[${date.toLocaleTimeString()}]</span> `;
            } catch(e) {}
            content = timeMatch[2];
        }
        
        // Clasificación por palabras clave
        let cssClass = 'log-line';
        const upper = content.toUpperCase();
        if (upper.includes('ERROR') || upper.includes('SEVERE') || upper.includes('FATAL') || upper.includes('EXCEPTION')) {
            cssClass += ' log-error';
        } else if (upper.includes('WARN')) {
            cssClass += ' log-warn';
        } else if (upper.includes('INFO')) {
            cssClass += ' log-info';
        }
        
        // Escapar HTML nativo para seguridad
        content = content.replace(/</g, "&lt;").replace(/>/g, "&gt;");
        
        formattedHtml += `<div class="${cssClass}">${timestamp}${content}</div>`;
    });
    
    return formattedHtml;
}

async function refreshLogs() {
    if (!currentLogServer) return;
    try {
        const res = await fetch(`/api/logs/${currentLogServer}`);
        const json = await res.json();
        const container = document.getElementById('logs-container');
        
        // Auto-scroll solo si el usuario ya estaba abajo leyendo (evita saltos molestos si está leyendo arriba)
        const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 50;

        if (json.status === 'success') {
            container.innerHTML = formatLogs(json.data);
            if (isAtBottom) {
                container.scrollTop = container.scrollHeight;
            }
        } else {
            container.innerHTML = `<div class="log-error">Error al cargar logs: ${json.message}</div>`;
        }
    } catch (e) {
        console.error("Fallo al obtener logs:", e);
    }
}

function closeLogsModal() {
    document.getElementById('logs-modal').classList.add('hidden');
    currentLogServer = null;
    if (logInterval) {
        clearInterval(logInterval);
        logInterval = null;
    }
}
