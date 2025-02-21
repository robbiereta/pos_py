// Variables globales
let clients = [];
let clientModal = null;
let clientSearchModal = null;

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar los modales
    const clientModalElement = document.getElementById('clientModal');
    const clientSearchModalElement = document.getElementById('clientSearchModal');
    
    if (clientModalElement) {
        clientModal = new bootstrap.Modal(clientModalElement);
    }
    
    if (clientSearchModalElement) {
        clientSearchModal = new bootstrap.Modal(clientSearchModalElement);
    }
    
    // Cargar clientes al mostrar la pestaña
    document.getElementById('clients-tab').addEventListener('shown.bs.tab', function (e) {
        loadClients();
    });

    // Event listener para búsqueda de clientes
    const searchInput = document.getElementById('clientSearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(searchClients, 300));
    }

    // Event listener para búsqueda en el modal
    const modalSearchInput = document.getElementById('clientSearchInput');
    if (modalSearchInput) {
        modalSearchInput.addEventListener('input', debounce(searchClientsModal, 300));
    }

    // Inicializar con el cliente público general
    selectPublicGeneral();
});

// Función para cargar clientes
function loadClients(search = '') {
    const loadingIndicator = document.getElementById('clientsLoading');
    const tableBody = document.querySelector('#clientsTable tbody');
    
    loadingIndicator.classList.remove('d-none');
    tableBody.classList.add('d-none');

    fetch(`/api/clients?search=${encodeURIComponent(search)}`)
        .then(response => response.json())
        .then(data => {
            clients = data;
            displayClients(clients);
        })
        .catch(error => {
            console.error('Error cargando clientes:', error);
            showToast('Error', 'Error al cargar los clientes', 'error');
        })
        .finally(() => {
            loadingIndicator.classList.add('d-none');
            tableBody.classList.remove('d-none');
        });
}

// Función para mostrar clientes en la tabla
function displayClients(clientsToShow) {
    const tbody = document.querySelector('#clientsTable tbody');
    tbody.innerHTML = '';

    if (clientsToShow.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="5" class="text-center">No se encontraron clientes</td>
        `;
        tbody.appendChild(row);
        return;
    }

    clientsToShow.forEach(client => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${client.name}</td>
            <td>${client.email || '-'}</td>
            <td>${client.phone || '-'}</td>
            <td>${client.rfc || '-'}</td>
            <td>
                <button class="btn btn-sm btn-primary me-2" onclick="openClientModal(${client.id})" title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteClient(${client.id})" title="Eliminar">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Función para buscar clientes
function searchClients() {
    const searchTerm = document.getElementById('clientSearch').value;
    loadClients(searchTerm);
}

// Función para abrir el modal de cliente
function openClientModal(clientId = null) {
    const form = document.getElementById('clientForm');
    const submitBtn = document.querySelector('#clientModal .btn-primary');
    
    form.reset();
    document.getElementById('clientId').value = '';
    document.getElementById('clientModalTitle').textContent = 'Nuevo Cliente';
    submitBtn.disabled = false;

    if (clientId) {
        const client = clients.find(c => c.id === clientId);
        if (client) {
            document.getElementById('clientModalTitle').textContent = 'Editar Cliente';
            document.getElementById('clientId').value = client.id;
            document.getElementById('clientName').value = client.name;
            document.getElementById('clientEmail').value = client.email || '';
            document.getElementById('clientPhone').value = client.phone || '';
            document.getElementById('clientRfc').value = client.rfc || '';
            document.getElementById('clientAddress').value = client.address || '';
        }
    }

    clientModal.show();
}

// Función para guardar cliente
function saveClient() {
    const submitBtn = document.querySelector('#clientModal .btn-primary');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Guardando...';

    const clientData = {
        id: document.getElementById('clientId').value,
        name: document.getElementById('clientName').value,
        email: document.getElementById('clientEmail').value,
        phone: document.getElementById('clientPhone').value,
        rfc: document.getElementById('clientRfc').value,
        address: document.getElementById('clientAddress').value
    };

    const method = clientData.id ? 'PUT' : 'POST';
    const url = clientData.id ? `/api/clients/${clientData.id}` : '/api/clients';

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(clientData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        clientModal.hide();
        loadClients();
        showToast('Éxito', 'Cliente guardado correctamente', 'success');
    })
    .catch(error => {
        console.error('Error guardando cliente:', error);
        showToast('Error', error.message || 'Error al guardar el cliente', 'error');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Guardar';
    });
}

// Función para eliminar cliente
function deleteClient(clientId) {
    if (!confirm('¿Está seguro de eliminar este cliente?')) {
        return;
    }

    const row = document.querySelector(`#clientsTable tr button[onclick*="${clientId}"]`).closest('tr');
    row.classList.add('table-danger');

    fetch(`/api/clients/${clientId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        row.remove();
        showToast('Éxito', 'Cliente eliminado correctamente', 'success');
        loadClients(); // Recargar la lista por si hay cambios en el orden
    })
    .catch(error => {
        console.error('Error eliminando cliente:', error);
        row.classList.remove('table-danger');
        showToast('Error', error.message || 'Error al eliminar el cliente', 'error');
    });
}

// Función para seleccionar el cliente público general
function selectPublicGeneral() {
    const publicGeneralClient = {
        id: 1,
        name: 'PUBLICO EN GENERAL',
        rfc: 'XAXX010101000',
        regimen_fiscal: '616',
        codigo_postal: '06000',
        uso_cfdi: 'S01'
    };
    
    updateSelectedClient(publicGeneralClient);
    
    // Cerrar modal si está abierto
    if (clientSearchModal) {
        clientSearchModal.hide();
    }
}

// Función para seleccionar un cliente específico
function selectClientForPOS(client) {
    updateSelectedClient(client);
    
    // Cerrar modal
    if (clientSearchModal) {
        clientSearchModal.hide();
    }
}

// Función para actualizar la información del cliente seleccionado
function updateSelectedClient(client) {
    document.getElementById('selectedClientId').value = client.id;
    document.getElementById('selectedClientName').textContent = client.name;
    document.getElementById('selectedClientRFC').textContent = `RFC: ${client.rfc}`;
    
    // Guardar datos completos para facturación
    window.selectedClientData = client;
}

// Función para buscar clientes en el modal
function searchClientsModal() {
    const searchInput = document.getElementById('clientSearchInput');
    const searchTerm = searchInput.value.trim();
    
    if (searchTerm === '') {
        return;
    }
    
    fetch(`/api/clients/search?q=${encodeURIComponent(searchTerm)}`)
        .then(response => response.json())
        .then(data => {
            const resultsContainer = document.getElementById('clientSearchResults');
            resultsContainer.innerHTML = '';
            
            if (data.length === 0) {
                resultsContainer.innerHTML = '<div class="list-group-item">No se encontraron resultados</div>';
                return;
            }
            
            data.forEach(client => {
                const item = document.createElement('button');
                item.className = 'list-group-item list-group-item-action';
                item.type = 'button';
                item.onclick = () => selectClientForPOS(client);
                
                item.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${client.name}</h6>
                            <p class="mb-1 small">RFC: ${client.rfc}</p>
                        </div>
                        <button class="btn btn-sm btn-primary">Seleccionar</button>
                    </div>
                `;
                
                resultsContainer.appendChild(item);
            });
        })
        .catch(error => {
            console.error('Error buscando clientes:', error);
            showToast('Error', 'Error al buscar clientes', 'error');
        });
}

// Función de utilidad para debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Función para mostrar notificaciones
function showToast(title, message, type = 'info') {
    // Implementar según el sistema de notificaciones que uses
    console.log(`${title}: ${message}`);
}
