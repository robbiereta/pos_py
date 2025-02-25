// Product Management

let productModal = null;
let currentProductId = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize product modal
    productModal = new bootstrap.Modal(document.getElementById('productModal'));
    
    // Initialize search input
    const searchInput = document.getElementById('productSearchInput');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                loadProducts(this.value);
            }, 300);
        });
    }
    
    // Load products when tab is shown
    const productTab = document.getElementById('product-tab');
    if (productTab) {
        productTab.addEventListener('shown.bs.tab', function() {
            loadProducts();
        });
    }
});

function loadProducts(searchQuery = '') {
    fetch(`/api/products?q=${encodeURIComponent(searchQuery)}`)
        .then(response => response.json())
        .then(products => {
            const tbody = document.getElementById('productsTableBody');
            tbody.innerHTML = '';
            
            products.forEach(product => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${product.sku || '-'}</td>
                    <td>${product.name}</td>
                    <td>$${product.price.toFixed(2)}</td>
                    <td>
                        <button class="btn btn-sm btn-primary me-1" onclick="editProduct('${product._id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteProduct('${product._id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error loading products:', error);
            showNotification('Error al cargar productos', 'error');
        });
}

function openProductModal(productId = null) {
    currentProductId = productId;
    const form = document.getElementById('productForm');
    form.reset();
    
    if (productId) {
        // Edit mode
        document.getElementById('productModalTitle').textContent = 'Editar Producto';
        fetch(`/api/products/${productId}`)
            .then(response => response.json())
            .then(product => {
                document.getElementById('productName').value = product.name;
                document.getElementById('productSku').value = product.sku || '';
                document.getElementById('productPrice').value = product.price;
            })
            .catch(error => {
                console.error('Error loading product:', error);
                showNotification('Error al cargar el producto', 'error');
            });
    } else {
        // Create mode
        document.getElementById('productModalTitle').textContent = 'Nuevo Producto';
    }
    
    productModal.show();
}

function saveProduct() {
    const productData = {
        name: document.getElementById('productName').value.trim(),
        sku: document.getElementById('productSku').value.trim(),
        price: parseFloat(document.getElementById('productPrice').value)
    };
    
    if (!productData.name) {
        showNotification('El nombre del producto es requerido', 'error');
        return;
    }
    
    const url = currentProductId ? 
        `/api/products/${currentProductId}` : 
        '/api/products';
        
    const method = currentProductId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(productData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(product => {
        productModal.hide();
        loadProducts();
        showNotification(
            currentProductId ? 
            'Producto actualizado exitosamente' : 
            'Producto creado exitosamente',
            'success'
        );
    })
    .catch(error => {
        console.error('Error saving product:', error);
        showNotification(error.error || 'Error al guardar el producto', 'error');
    });
}

function deleteProduct(productId) {
    if (!confirm('¿Está seguro de que desea eliminar este producto?')) {
        return;
    }
    
    fetch(`/api/products/${productId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(() => {
        loadProducts();
        showNotification('Producto eliminado exitosamente', 'success');
    })
    .catch(error => {
        console.error('Error deleting product:', error);
        showNotification(error.error || 'Error al eliminar el producto', 'error');
    });
}
