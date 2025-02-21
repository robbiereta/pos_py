// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize event listeners
    initializeEventListeners();
    
    // Load initial data
    loadProducts();
    
    // Update reprint button visibility
    updateReprintButton();
});

function initializeEventListeners() {
    // Sales tab listener
    const salesTab = document.getElementById('sales-tab');
    if (salesTab) {
        salesTab.addEventListener('shown.bs.tab', function (e) {
            loadSales();
        });
    }

    // Sales filter form listener
    const salesFilterForm = document.getElementById('salesFilterForm');
    if (salesFilterForm) {
        salesFilterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const filters = {
                startDate: document.getElementById('startDate').value,
                endDate: document.getElementById('endDate').value,
                invoiced: document.getElementById('invoicedFilter').value
            };
            loadSales(filters);
        });
    }

    // Product search listener with debounce
    const searchInput = document.getElementById('productSearch');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchProducts();
            }, 300);
        });
    }
}
