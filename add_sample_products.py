from app import create_app, db
from models import Product

app = create_app('development')

with app.app_context():
    # Create sample products
    products = [
        Product(name='Laptop', price=15000.00, stock=10),
        Product(name='Mouse', price=299.99, stock=20),
        Product(name='Keyboard', price=599.99, stock=15),
        Product(name='Monitor', price=3999.99, stock=8),
        Product(name='Headphones', price=899.99, stock=25)
    ]
    
    # Add products to database
    for product in products:
        db.session.add(product)
    
    # Commit changes
    db.session.commit()
    
    print("\nAdded Products:")
    print("-" * 50)
    for product in products:
        print(f"ID: {product.id}, Name: {product.name}, Price: ${product.price:.2f}, Stock: {product.stock}")
