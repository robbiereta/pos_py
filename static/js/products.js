// Product Management

let productModal = null;
let currentProductId = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize product modal
    const modalElement = document.getElementById('productModal');
    if (modalElement && typeof bootstrap !== 'undefined') {
        try {
            productModal = new bootstrap.Modal(modalElement);
        } catch (error) {
            console.error('Error initializing product modal:', error);
        }
    }
    
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
    
    // Load products initially if we're on the product management tab
    if (document.getElementById('productsTableBody')) {
        loadProducts();
    }
    
    // Configure track stock checkbox
    const trackStockCheckbox = document.getElementById('trackStock');
    if (trackStockCheckbox) {
        trackStockCheckbox.addEventListener('change', function() {
            toggleStockField(this.checked);
        });
    }
});

// Function to toggle stock field visibility
function toggleStockField(show) {
    const stockContainer = document.getElementById('stockFieldContainer');
    if (stockContainer) {
        stockContainer.style.display = show ? 'block' : 'none';
        
        // If not tracking stock, set value to 0
        if (!show) {
            document.getElementById('productStock').value = '0';
        }
    }
}

function loadProducts(searchQuery = '') {
    console.log('Cargando productos con búsqueda:', searchQuery);
    fetch(`/api/products?q=${encodeURIComponent(searchQuery)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }
            return response.json();
        })
        .then(products => {
            const tbody = document.getElementById('productsTableBody');
            if (!tbody) {
                console.error('No se encontró el elemento productsTableBody');
                return;
            }
            
            tbody.innerHTML = '';
            
            if (products.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay productos</td></tr>';
                return;
            }
            
            products.forEach(product => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${product.sku || '-'}</td>
                    <td>${product.name}</td>
                    <td>$${parseFloat(product.price).toFixed(2)}</td>
                    <td>${product.track_stock ? (product.stock || 0) : 'Sin contar'}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="openProductModal('${product._id}')">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="deleteProduct('${product._id}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error loading products:', error);
            alert('Error al cargar los productos. Por favor, inténtalo de nuevo.');
        });
}

function openProductModal(productId = null) {
    console.log('Abriendo modal de producto con ID:', productId);
    currentProductId = productId;
    
    // Clear form
    document.getElementById('productName').value = '';
    document.getElementById('productSku').value = '';
    document.getElementById('productPrice').value = '';
    document.getElementById('productStock').value = '0';
    document.getElementById('trackStock').checked = true;
    
    // Show stock field by default
    toggleStockField(true);
    
    // Change modal title based on mode (add/edit)
    const modalTitle = document.querySelector('#productModal .modal-title');
    
    if (productId) {
        modalTitle.textContent = 'Editar Producto';
        
        // Fetch product data
        fetch(`/api/products/${productId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error en la respuesta del servidor');
                }
                return response.json();
            })
            .then(product => {
                document.getElementById('productName').value = product.name;
                document.getElementById('productSku').value = product.sku || '';
                document.getElementById('productPrice').value = product.price;
                document.getElementById('productStock').value = product.stock || 0;
                
                // Set track stock checkbox
                const trackStockCheckbox = document.getElementById('trackStock');
                if (trackStockCheckbox) {
                    const trackStock = product.track_stock !== undefined ? product.track_stock : true;
                    trackStockCheckbox.checked = trackStock;
                    toggleStockField(trackStock);
                }
            })
            .catch(error => {
                console.error('Error loading product details:', error);
                alert('Error al cargar los detalles del producto.');
                if (productModal) productModal.hide();
            });
    } else {
        modalTitle.textContent = 'Agregar Producto';
    }
    
    if (productModal) {
        productModal.show();
    } else {
        console.error('Modal no inicializado');
        alert('Error al abrir el modal. Por favor, recarga la página.');
    }
}

function saveProduct() {
    const name = document.getElementById('productName').value.trim();
    const sku = document.getElementById('productSku').value.trim();
    const price = parseFloat(document.getElementById('productPrice').value) || 0;
    const trackStock = document.getElementById('trackStock').checked;
    const stock = parseInt(document.getElementById('productStock').value) || 0;
    
    if (!name) {
        alert('El nombre del producto es obligatorio.');
        return;
    }
    
    const productData = {
        name,
        sku,
        price,
        stock,
        track_stock: trackStock
    };
    
    const url = currentProductId 
        ? `/api/products/${currentProductId}`
        : '/api/products';
        
    const method = currentProductId ? 'PUT' : 'POST';
    
    console.log('Guardando producto con método:', method);
    console.log('Datos del producto:', productData);
    
    fetch(url, {
        method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(productData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { 
                throw new Error(err.error || 'Error al guardar el producto');
            });
        }
        return response.json();
    })
    .then(data => {
        if (productModal) productModal.hide();
        loadProducts();
        alert(currentProductId ? 'Producto actualizado con éxito' : 'Producto creado con éxito');
    })
    .catch(error => {
        console.error('Error saving product:', error);
        alert(error.message || 'Error al guardar el producto. Por favor, inténtalo de nuevo.');
    });
}

function deleteProduct(productId) {
    if (!confirm('¿Estás seguro de que deseas eliminar este producto?')) {
        return;
    }
    
    console.log('Eliminando producto con ID:', productId);
    
    fetch(`/api/products/${productId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { 
                throw new Error(err.error || 'Error al eliminar el producto');
            });
        }
        return response.json();
    })
    .then(data => {
        loadProducts();
        alert('Producto eliminado con éxito');
    })
    .catch(error => {
        console.error('Error deleting product:', error);
        alert(error.message || 'Error al eliminar el producto. Por favor, inténtalo de nuevo.');
    });
}
