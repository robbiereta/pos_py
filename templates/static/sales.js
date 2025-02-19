// Variables globales
let currentPage = 1;
const perPage = 10;

// Funciones de utilidad
const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleString('es-MX');
};

const formatMoney = (amount) => {
    return parseFloat(amount).toLocaleString('es-MX', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
};

const formatProducts = (products) => {
    let productsArray = [];
    try {
        productsArray = typeof products === 'string' ? JSON.parse(products) : products;
    } catch (e) {
        console.error('Error parsing products:', e);
        return '0 productos';
    }
    return `${productsArray.length} producto(s)`;
};

// Cargar estadísticas
const loadStats = async (filters = {}) => {
    try {
        let url = '/sales/stats';
        const params = new URLSearchParams();
        if (filters.startDate) params.append('start_date', filters.startDate);
        if (filters.endDate) params.append('end_date', filters.endDate);
        if (params.toString()) url += '?' + params.toString();

        const response = await fetch(url);
        const data = await response.json();

        // Actualizar estadísticas en la UI
        document.getElementById('statTotalSales').textContent = data.total_sales;
        document.getElementById('statTotalAmount').textContent = formatMoney(data.total_amount);
        document.getElementById('statAvgAmount').textContent = formatMoney(data.average_amount);
        document.getElementById('statMaxAmount').textContent = formatMoney(data.max_amount);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
};

// Cargar ventas
const loadSales = async (page = 1, filters = {}) => {
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: perPage
        });

        // Agregar filtros si existen
        if (filters.startDate) params.append('start_date', filters.startDate);
        if (filters.endDate) params.append('end_date', filters.endDate);
        if (filters.minAmount) params.append('min_amount', filters.minAmount);
        if (filters.maxAmount) params.append('max_amount', filters.maxAmount);

        const response = await fetch(`/sales?${params.toString()}`);
        const data = await response.json();

        // Limpiar tabla
        const salesList = document.getElementById('salesList');
        salesList.innerHTML = '';

        // Agregar ventas
        data.sales.forEach(sale => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${sale.id}</td>
                <td>${formatDate(sale.timestamp)}</td>
                <td>$${formatMoney(sale.total_amount)}</td>
                <td>${formatProducts(sale.products)}</td>
                <td>
                    <span class="badge ${sale.is_invoiced ? 'bg-success' : 'bg-warning'}">
                        ${sale.is_invoiced ? 'Facturado' : 'Pendiente'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="showSaleDetail(${sale.id})">
                        <i class="bi bi-eye"></i>
                    </button>
                    ${!sale.is_invoiced ? `
                        <button class="btn btn-sm btn-danger" onclick="deleteSale(${sale.id})">
                            <i class="bi bi-trash"></i>
                        </button>
                    ` : ''}
                </td>
            `;
            salesList.appendChild(row);
        });

        // Actualizar paginación
        updatePagination(data.current_page, data.total_pages);
        currentPage = page;

    } catch (error) {
        console.error('Error loading sales:', error);
    }
};

// Actualizar paginación
const updatePagination = (currentPage, totalPages) => {
    const pagination = document.getElementById('salesPagination');
    pagination.innerHTML = '';

    // Botón anterior
    const prevBtn = document.createElement('li');
    prevBtn.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevBtn.innerHTML = `
        <a class="page-link" href="#" onclick="loadSales(${currentPage - 1})">Anterior</a>
    `;
    pagination.appendChild(prevBtn);

    // Páginas
    for (let i = 1; i <= totalPages; i++) {
        if (
            i === 1 || 
            i === totalPages || 
            (i >= currentPage - 2 && i <= currentPage + 2)
        ) {
            const pageBtn = document.createElement('li');
            pageBtn.className = `page-item ${i === currentPage ? 'active' : ''}`;
            pageBtn.innerHTML = `
                <a class="page-link" href="#" onclick="loadSales(${i})">${i}</a>
            `;
            pagination.appendChild(pageBtn);
        } else if (
            i === currentPage - 3 || 
            i === currentPage + 3
        ) {
            const ellipsis = document.createElement('li');
            ellipsis.className = 'page-item disabled';
            ellipsis.innerHTML = '<a class="page-link">...</a>';
            pagination.appendChild(ellipsis);
        }
    }

    // Botón siguiente
    const nextBtn = document.createElement('li');
    nextBtn.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextBtn.innerHTML = `
        <a class="page-link" href="#" onclick="loadSales(${currentPage + 1})">Siguiente</a>
    `;
    pagination.appendChild(nextBtn);
};

// Mostrar detalle de venta
const showSaleDetail = async (saleId) => {
    try {
        const response = await fetch(`/sales/${saleId}`);
        const sale = await response.json();

        // Actualizar modal con los datos de la venta
        document.getElementById('modalSaleId').textContent = sale.id;
        document.getElementById('modalSaleDate').textContent = formatDate(sale.timestamp);
        document.getElementById('modalSaleAmount').textContent = formatMoney(sale.total_amount);
        document.getElementById('modalSaleStatus').textContent = sale.is_invoiced ? 'Facturado' : 'Pendiente';

        // Mostrar productos
        const productsTable = document.getElementById('modalSaleProducts');
        productsTable.innerHTML = '';

        const products = typeof sale.products === 'string' ? JSON.parse(sale.products) : sale.products;
        products.forEach(product => {
            const row = document.createElement('tr');
            const subtotal = product.price * product.quantity;
            row.innerHTML = `
                <td>${product.id}</td>
                <td>${product.quantity}</td>
                <td>$${formatMoney(product.price)}</td>
                <td>$${formatMoney(subtotal)}</td>
            `;
            productsTable.appendChild(row);
        });

        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('saleDetailModal'));
        modal.show();

    } catch (error) {
        console.error('Error loading sale details:', error);
    }
};

// Eliminar venta
const deleteSale = async (saleId) => {
    if (!confirm('¿Estás seguro de que deseas eliminar esta venta?')) {
        return;
    }

    try {
        const response = await fetch(`/sales/${saleId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            // Recargar ventas y estadísticas
            loadSales(currentPage);
            loadStats();
            alert('Venta eliminada exitosamente');
        } else {
            const data = await response.json();
            alert(data.error || 'Error al eliminar la venta');
        }
    } catch (error) {
        console.error('Error deleting sale:', error);
        alert('Error al eliminar la venta');
    }
};

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Cargar datos iniciales
    loadStats();
    loadSales(1);

    // Manejar filtros
    document.getElementById('salesFilterForm').addEventListener('submit', (e) => {
        e.preventDefault();
        
        const filters = {
            startDate: document.getElementById('startDate').value,
            endDate: document.getElementById('endDate').value,
            minAmount: document.getElementById('minAmount').value,
            maxAmount: document.getElementById('maxAmount').value
        };

        loadStats(filters);
        loadSales(1, filters);
    });

    // Manejar reset de filtros
    document.getElementById('salesFilterForm').addEventListener('reset', () => {
        setTimeout(() => {
            loadStats();
            loadSales(1);
        }, 0);
    });
});
