// Configuración de gráficos
let ventasDiariasChart = null;
let distribucionVentasChart = null;

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
function updateMonthSelector() {
    const monthSelect = document.getElementById('monthSelector');
    const yearSelect = document.getElementById('yearSelector');
    
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

// Función para cambiar el mes
function changeMonth() {
    const year = document.getElementById('yearSelector').value;
    const month = document.getElementById('monthSelector').value;
    const dates = getDaysInMonth(year, month);
    
    // Actualizar el daterangepicker
    $('#dateRange').data('daterangepicker').setStartDate(dates.start);
    $('#dateRange').data('daterangepicker').setEndDate(dates.end);
    
    // Actualizar el dashboard
    updateDashboard();
}

// Inicializar selector de fechas
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar DateRangePicker
    $('#dateRange').daterangepicker({
        startDate: moment().startOf('month'),
        endDate: moment().endOf('month'),
        ranges: {
           'Hoy': [moment(), moment()],
           'Ayer': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
           'Últimos 7 días': [moment().subtract(6, 'days'), moment()],
           'Últimos 30 días': [moment().subtract(29, 'days'), moment()],
           'Este mes': [moment().startOf('month'), moment().endOf('month')],
           'Mes pasado': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        },
        locale: {
            format: 'DD/MM/YYYY',
            applyLabel: 'Aplicar',
            cancelLabel: 'Cancelar',
            customRangeLabel: 'Rango personalizado'
        }
    });

    // Inicializar el dashboard cuando se muestra el tab
    $('a[data-bs-toggle="tab"]').on('shown.bs.tab', function (e) {
        if (e.target.id === 'dashboard-tab') {
            updateDashboard();
        }
    });

    // Actualizar al hacer clic en el botón
    $('#updateDashboard').click(updateDashboard);
    
    // Actualizar selector de mes
    updateMonthSelector();
    
    // Agregar evento de cambio de mes
    document.getElementById('monthSelector').addEventListener('change', changeMonth);
    document.getElementById('yearSelector').addEventListener('change', changeMonth);
});

// Función para formatear moneda
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN'
    }).format(amount);
}

// Función para actualizar el dashboard
function updateDashboard() {
    const dates = $('#dateRange').val().split(' - ');
    fetch(`/daily_summary?start_date=${dates[0]}&end_date=${dates[1]}`)
        .then(response => response.json())
        .then(data => {
            // Actualizar resumen general
            $('#totalVentas').text(data.resumen_general.total_ventas);
            $('#montoTotal').text(formatCurrency(data.resumen_general.total_monto));
            $('#promedioDiario').text(formatCurrency(data.resumen_general.promedio_diario));
            $('#diasVentas').text(data.resumen_general.total_dias);

            // Actualizar tabla de resumen diario
            const tbody = $('#resumenDiarioTable tbody');
            tbody.empty();
            data.resumen_diario.forEach(dia => {
                tbody.append(`
                    <tr>
                        <td>${dia.fecha}</td>
                        <td>${dia.total_ventas}</td>
                        <td>${formatCurrency(dia.monto_total)}</td>
                        <td>${formatCurrency(dia.venta_minima)}</td>
                        <td>${formatCurrency(dia.venta_maxima)}</td>
                        <td>${formatCurrency(dia.promedio_venta)}</td>
                        <td>
                            <button class="btn btn-sm btn-info" onclick='mostrarDetalles(${JSON.stringify(dia)})'>
                                <i class="fas fa-search"></i> Ver Detalles
                            </button>
                        </td>
                    </tr>
                `);
            });

            // Actualizar gráfico de ventas diarias
            const fechas = data.resumen_diario.map(d => d.fecha);
            const montos = data.resumen_diario.map(d => d.monto_total);
            const cantidades = data.resumen_diario.map(d => d.total_ventas);

            if (ventasDiariasChart) {
                ventasDiariasChart.destroy();
            }
            ventasDiariasChart = new Chart(document.getElementById('ventasDiariasChart'), {
                type: 'bar',
                data: {
                    labels: fechas,
                    datasets: [{
                        label: 'Monto Total',
                        data: montos,
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1,
                        yAxisID: 'y'
                    }, {
                        label: 'Cantidad de Ventas',
                        data: cantidades,
                        type: 'line',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 2,
                        fill: false,
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            type: 'linear',
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Monto Total'
                            }
                        },
                        y1: {
                            type: 'linear',
                            position: 'right',
                            title: {
                                display: true,
                                text: 'Cantidad de Ventas'
                            },
                            grid: {
                                drawOnChartArea: false
                            }
                        }
                    }
                }
            });

            // Actualizar gráfico de distribución
            const rangos = {
                '0-100': 0,
                '101-500': 0,
                '501-1000': 0,
                '1001+': 0
            };

            data.resumen_diario.forEach(dia => {
                if (dia.monto_total <= 100) rangos['0-100']++;
                else if (dia.monto_total <= 500) rangos['101-500']++;
                else if (dia.monto_total <= 1000) rangos['501-1000']++;
                else rangos['1001+']++;
            });

            if (distribucionVentasChart) {
                distribucionVentasChart.destroy();
            }
            distribucionVentasChart = new Chart(document.getElementById('distribucionVentasChart'), {
                type: 'pie',
                data: {
                    labels: Object.keys(rangos),
                    datasets: [{
                        data: Object.values(rangos),
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.5)',
                            'rgba(54, 162, 235, 0.5)',
                            'rgba(255, 206, 86, 0.5)',
                            'rgba(75, 192, 192, 0.5)'
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(75, 192, 192, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right'
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error al actualizar el dashboard:', error);
            alert('Error al cargar los datos del dashboard');
        });
}

// Función para mostrar detalles
function mostrarDetalles(dia) {
    const tbody = $('#detallesTable tbody');
    tbody.empty();
    dia.productos.forEach(prod => {
        tbody.append(`
            <tr>
                <td>Producto #${prod.id}</td>
                <td>${prod.cantidad}</td>
                <td>${formatCurrency(prod.total)}</td>
                <td>${formatCurrency(prod.promedio)}</td>
            </tr>
        `);
    });
    new bootstrap.Modal(document.getElementById('detallesModal')).show();
}
