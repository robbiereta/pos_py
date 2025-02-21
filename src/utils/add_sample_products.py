from app import create_app, db
from models import Product
from datetime import datetime

def add_sample_products():
    app = create_app('development')
    
    # Lista de productos de ejemplo
    sample_products = [
        {
            "name": "Coca Cola 600ml",
            "price": 18.50,
            "stock": 50,
            "description": "Refresco Coca Cola botella 600ml",
            "sku": "COC-600",
            "min_stock": 10
        },
        {
            "name": "Sabritas Original 45g",
            "price": 15.00,
            "stock": 40,
            "description": "Papas fritas Sabritas sabor original",
            "sku": "SAB-045",
            "min_stock": 8
        },
        {
            "name": "Pan Bimbo Grande",
            "price": 45.00,
            "stock": 25,
            "description": "Pan blanco Bimbo presentación familiar",
            "sku": "BIM-001",
            "min_stock": 5
        },
        {
            "name": "Leche Alpura 1L",
            "price": 28.50,
            "stock": 30,
            "description": "Leche entera Alpura 1 litro",
            "sku": "ALP-1L",
            "min_stock": 10
        },
        {
            "name": "Jabón Zote 400g",
            "price": 22.00,
            "stock": 35,
            "description": "Jabón de lavandería Zote rosa",
            "sku": "ZOT-400",
            "min_stock": 8
        }
    ]

    with app.app_context():
        # Eliminar productos existentes
        Product.query.delete()
        
        # Agregar nuevos productos
        for product_data in sample_products:
            product = Product(
                name=product_data["name"],
                price=product_data["price"],
                stock=product_data["stock"],
                description=product_data["description"],
                sku=product_data["sku"],
                min_stock=product_data["min_stock"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(product)
        
        # Guardar cambios
        db.session.commit()
        print("¡Productos de ejemplo agregados exitosamente!")

if __name__ == "__main__":
    add_sample_products()
