// Función para obtener el primer y último día del mes
function getDaysInMonth(year, month) {
    const startDate = moment([year, month - 1, 1]);
    const endDate = moment(startDate).endOf('month');
    return {
        start: startDate.format('YYYY-MM-DD'),
        end: endDate.format('YYYY-MM-DD')
    };
}

// Función para actualizar el selector de mes
function updateInvoiceMonthSelector() {
    const monthSelect = document.getElementById('invoiceMonthSelector');
    const yearSelect = document.getElementById('invoiceYearSelector');
    
    if (!monthSelect || !yearSelect) return;

    const currentDate = moment();
    const currentYear = currentDate.year();
    
    // Generar años (desde 2020 hasta el año actual)
    yearSelect.innerHTML = '';
    for (let year = currentYear; year >= 2020; year--) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        if (year === currentYear) {
            option.selected = true;
        }
        yearSelect.appendChild(option);
    }
    
    // Generar meses
    const months = moment.months();
    monthSelect.innerHTML = '';
    months.forEach((month, index) => {
        const option = document.createElement('option');
        option.value = index + 1;
        option.textContent = month;
        if (index + 1 === currentDate.month() + 1) {
            option.selected = true;
        }
        monthSelect.appendChild(option);
    });
}

// Función para formatear moneda
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN'
    }).format(amount);
}

// Función para previsualizar la factura global
function previewGlobalInvoice() {
    const year = document.getElementById('invoiceYearSelector').value;
    const month = document.getElementById('invoiceMonthSelector').value;
    const dates = getDaysInMonth(year, month);
    
    fetch('/generate_global_invoice', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            start_date: dates.start,
            end_date: dates.end
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        
        // Mostrar la vista previa
        document.getElementById('invoicePreview').style.display = 'block';
        
        // Actualizar información del período
        const monthName = moment.months()[month - 1];
        document.getElementById('invoicePeriod').textContent = `${monthName} ${year}`;
        document.getElementById('invoiceTotalSales').textContent = data.invoice_data.total_ventas;
        document.getElementById('invoiceTotalAmount').textContent = formatCurrency(data.invoice_data.monto_total);
        
        // Actualizar tabla de productos
        const tbody = document.getElementById('invoiceProductsTable').getElementsByTagName('tbody')[0];
        tbody.innerHTML = '';
        
        data.invoice_data.productos.forEach(producto => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>Producto #${producto.id}</td>
                <td>${producto.cantidad}</td>
                <td>${formatCurrency(producto.precio_unitario)}</td>
                <td>${formatCurrency(producto.importe)}</td>
            `;
            tbody.appendChild(tr);
        });
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al generar la vista previa de la factura');
    });
}

// Función para generar la factura global
function generateGlobalInvoice() {
    const year = document.getElementById('invoiceYearSelector').value;
    const month = document.getElementById('invoiceMonthSelector').value;
    const dates = getDaysInMonth(year, month);
    
    if (!confirm('¿Estás seguro de que deseas generar la factura global? Esta acción no se puede deshacer.')) {
        return;
    }
    
    fetch('/generate_global_invoice', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            start_date: dates.start,
            end_date: dates.end,
            generate: true
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        
        alert('Factura global generada correctamente');
        document.getElementById('invoicePreview').style.display = 'none';
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al generar la factura global');
    });
}

// Eventos
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar selectores
    updateInvoiceMonthSelector();
    
    // Evento para vista previa
    document.getElementById('previewGlobalInvoice').addEventListener('click', previewGlobalInvoice);
    
    // Evento para generar factura
    document.getElementById('generateGlobalInvoice').addEventListener('click', generateGlobalInvoice);
    
    // Eventos de cambio de mes/año
    document.getElementById('invoiceMonthSelector').addEventListener('change', () => {
        document.getElementById('invoicePreview').style.display = 'none';
    });
    document.getElementById('invoiceYearSelector').addEventListener('change', () => {
        document.getElementById('invoicePreview').style.display = 'none';
    });
});
