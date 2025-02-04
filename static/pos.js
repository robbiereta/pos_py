document.addEventListener('DOMContentLoaded', () => {
    const productList = document.getElementById('productList');
    const cartList = document.getElementById('cartList');
    const totalAmountSpan = document.getElementById('totalAmount');
    const addProductForm = document.getElementById('addProductForm');
    const checkoutBtn = document.getElementById('checkoutBtn');
    const generateInvoiceCheckbox = document.getElementById('generateInvoice');
    const pendingSalesList = document.getElementById('pendingSalesList');
    const globalInvoiceList = document.getElementById('globalInvoiceList');
    const generateGlobalInvoiceBtn = document.getElementById('generateGlobalInvoiceBtn');
    const invoiceDateInput = document.getElementById('invoiceDate');

    if (invoiceDateInput) {
        const today = new Date().toISOString().split('T')[0];
        invoiceDateInput.value = today;
    }

    let products = [];
    let cart = [];

    // Fetch and display products
    async function loadProducts() {
        const response = await fetch('/products');
        products = await response.json();
        productList.innerHTML = products.map(product => `
            <tr>
                <td>${product.name}</td>
                <td>$${product.price.toFixed(2)}</td>
                <td>${product.stock}</td>
                <td>
                    <button class="btn btn-sm btn-success add-to-cart" data-id="${product.id}">
                        Agregar
                    </button>
                </td>
            </tr>
        `).join('');

        document.querySelectorAll('.add-to-cart').forEach(btn => {
            btn.addEventListener('click', addToCart);
        });
    }

    function addToCart(event) {
        const productId = event.target.dataset.id;
        const product = products.find(p => p.id == productId);
        
        const existingCartItem = cart.find(item => item.product.id === product.id);
        if (existingCartItem) {
            existingCartItem.quantity += 1;
        } else {
            cart.push({ product, quantity: 1 });
        }

        updateCart();
    }

    function updateCart() {
        const total = cart.reduce((sum, item) => sum + item.product.price * item.quantity, 0);
        totalAmountSpan.textContent = total.toFixed(2);

        cartList.innerHTML = cart.map(item => `
            <tr>
                <td>${item.product.name}</td>
                <td>${item.quantity}</td>
                <td>$${(item.product.price * item.quantity).toFixed(2)}</td>
            </tr>
        `).join('');
    }

    // Add new product
    addProductForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const newProduct = {
            name: document.getElementById('productName').value,
            price: parseFloat(document.getElementById('productPrice').value),
            stock: parseInt(document.getElementById('productStock').value)
        };

        const response = await fetch('/products', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newProduct)
        });

        const result = await response.json();
        if (result.status === 'success') {
            loadProducts();
            new bootstrap.Modal(document.getElementById('addProductModal')).hide();
        }
    });

    // Checkout
    checkoutBtn.addEventListener('click', async () => {
        const saleData = {
            total_amount: parseFloat(totalAmountSpan.textContent),
            products: cart.map(item => ({
                product_id: item.product.id,
                quantity: item.quantity,
                price: item.product.price,
                name: item.product.name
            })),
            generate_invoice: generateInvoiceCheckbox.checked
        };

        const response = await fetch('/sale', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(saleData)
        });

        const result = await response.json();
        if (result.cfdi_invoice) {
            alert(`Factura CFDI generada. UUID: ${result.cfdi_invoice.uuid}`);
        } else {
            alert('Venta registrada correctamente');
        }

        // Reset cart
        cart = [];
        updateCart();
        loadPendingSales();
    });

    // Load pending sales
    async function loadPendingSales() {
        const response = await fetch('/global-invoice/pending-sales');
        const sales = await response.json();
        
        pendingSalesList.innerHTML = sales.map(sale => `
            <tr>
                <td>${sale.id}</td>
                <td>${new Date(sale.timestamp).toLocaleString()}</td>
                <td>$${sale.total_amount.toFixed(2)}</td>
            </tr>
        `).join('');
    }

    // Load global invoice history
    async function loadGlobalInvoices() {
        const response = await fetch('/global-invoice/history');
        const invoices = await response.json();
        
        globalInvoiceList.innerHTML = invoices.map(invoice => `
            <tr>
                <td>${new Date(invoice.date).toLocaleDateString()}</td>
                <td>${invoice.cfdi_uuid}</td>
                <td>$${invoice.total_amount.toFixed(2)}</td>
                <td>$${invoice.tax_amount.toFixed(2)}</td>
            </tr>
        `).join('');
    }

    // Generate global invoice
    generateGlobalInvoiceBtn.addEventListener('click', async () => {
        const response = await fetch('/global-invoice/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: invoiceDateInput.value
            })
        });

        const result = await response.json();
        if (result.error) {
            alert(`Error: ${result.error}`);
        } else {
            alert(`Factura Global generada. UUID: ${result.cfdi_uuid}`);
            loadPendingSales();
            loadGlobalInvoices();
        }
    });

    // Tab change handler
    document.getElementById('global-invoice-tab').addEventListener('click', () => {
        loadPendingSales();
        loadGlobalInvoices();
    });

    // Initial load
    loadProducts();
});
