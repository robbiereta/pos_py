from app import app, db
from models import Product, Sale, Invoice, GlobalInvoice
from datetime import datetime, timedelta
import json
from cfdi_generator import cfdi_generator, cfdi_generator_prod

def create_test_products():
    """Create test products if they don't exist"""
    products = [
        {"name": "Laptop", "price": 15000.0},
        {"name": "Mouse", "price": 299.99},
        {"name": "Keyboard", "price": 599.99},
        {"name": "Monitor", "price": 3999.99},
        {"name": "Headphones", "price": 899.99}
    ]
    
    for product_data in products:
        product = Product.query.filter_by(name=product_data["name"]).first()
        if not product:
            product = Product(name=product_data["name"], price=product_data["price"])
            db.session.add(product)
    
    db.session.commit()

def create_test_sales():
    """Create some test sales"""
    sales_data = [
        [
            {"id": 1, "name": "Laptop", "price": 15000.0, "quantity": 1},
            {"id": 2, "name": "Mouse", "price": 299.99, "quantity": 1}
        ],
        [
            {"id": 3, "name": "Keyboard", "price": 599.99, "quantity": 2},
            {"id": 5, "name": "Headphones", "price": 899.99, "quantity": 1}
        ],
        [
            {"id": 4, "name": "Monitor", "price": 3999.99, "quantity": 1}
        ]
    ]
    
    for products in sales_data:
        total_amount = sum(product["price"] * product["quantity"] for product in products)
        sale = Sale(total_amount=total_amount, products=products)
        db.session.add(sale)
        print(f"Sale ID: {sale.id}")
        print(f"Total Amount: ${total_amount}")
        print(f"Products: {json.dumps(products, indent=2)}")
        print(f"Timestamp: {sale.timestamp}")
        print("-" * 50)
    
    db.session.commit()

def test_individual_invoice(test_mode=True):
    """Test generating individual invoices"""
    print(f"\nTesting Individual Invoice Generation (Mode: {'Test' if test_mode else 'Production'}):")
    print("-" * 50)
    
    # Get a sale that hasn't been invoiced
    sale = Sale.query.filter_by(is_invoiced=False).first()
    if not sale:
        print("No uninvoiced sales found")
        return
    
    try:
        generator = cfdi_generator if test_mode else cfdi_generator_prod
        result = generator.generate_cfdi(sale)
        print(f"Generated invoice for sale {sale.id}")
        print(f"UUID: {result['uuid']}")
        print(f"XML Sample: {result['xml'][:200]}...")  # Show first 200 chars of XML
    except Exception as e:
        print(json.dumps({"error": str(e)}))
    
    print("-" * 50)

def test_global_invoice(test_mode=True):
    """Test generating global invoice"""
    print(f"\nTesting Global Invoice Generation (Mode: {'Test' if test_mode else 'Production'}):")
    print("-" * 50)
    
    # Get all uninvoiced sales
    sales = Sale.query.filter_by(is_invoiced=False).all()
    print(f"Found {len(sales)} pending sales for global invoice")
    
    if not sales:
        print("No uninvoiced sales found")
        return
    
    try:
        date = datetime.now().date()
        generator = cfdi_generator if test_mode else cfdi_generator_prod
        result = generator.generate_global_cfdi(sales, date)
        print(f"Generated global invoice for {len(sales)} sales")
        print(f"UUID: {result['cfdi_uuid']}")
        print(f"XML Sample: {result['xml_content'][:200]}...")  # Show first 200 chars of XML
    except Exception as e:
        print(json.dumps({"error": str(e)}))
    
    print("-" * 50)

def main():
    """Main test function"""
    print("Starting POS System Test")
    print("=" * 50)
    print("\nCreated Test Sales:")
    print("-" * 50)
    
    with app.app_context():
        # Create test data
        create_test_products()
        create_test_sales()
        
        # Test invoice generation in test mode
        test_individual_invoice(test_mode=True)
        test_global_invoice(test_mode=True)
        
        # Test invoice generation in production mode
        test_individual_invoice(test_mode=False)
        test_global_invoice(test_mode=False)
    
    print("\nTest Complete!")

if __name__ == "__main__":
    main()
