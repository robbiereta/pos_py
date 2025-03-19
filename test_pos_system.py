from app import create_app
from db import get_db
from models import Product, Sale, Invoice, GlobalInvoice
from datetime import datetime, timedelta
import json
from cfdi_generator import CFDIGenerator

def create_test_products():
    """Create test products if they don't exist"""
    products = [
        {"name": "Laptop", "price": 15000.0},
        {"name": "Mouse", "price": 299.99},
        {"name": "Keyboard", "price": 599.99},
        {"name": "Monitor", "price": 3999.99},
        {"name": "Headphones", "price": 899.99}
    ]
    
    db = get_db()
    for product_data in products:
        product = db.products.find_one({"name": product_data["name"]})
        if not product:
            Product.create_product(db, **product_data)
    
    print("Created test products")

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
    
    db = get_db()
    for products in sales_data:
        total_amount = sum(product["price"] * product["quantity"] for product in products)
        Sale.create_sale(
            db=db,
            client_id="65d7e68fcb2f40dff539796d",  # Test client ID
            total_amount=total_amount,
            amount_received=total_amount,
            change_amount=0,
            details=products
        )
        print(f"Created sale with total amount: ${total_amount:,.2f}")
        print(f"Products: {json.dumps(products, indent=2)}")
        print("-" * 50)

def test_individual_invoice(test_mode=True):
    """Test generating individual invoices"""
    print(f"\nTesting Individual Invoice Generation (Mode: {'Test' if test_mode else 'Production'}):")
    print("-" * 50)
    
    db = get_db()
    # Get a sale that hasn't been invoiced
    sale = db.sales.find_one({"is_invoiced": False})
    if not sale:
        print("No uninvoiced sales found")
        return
    
    try:
        generator = CFDIGenerator(test_mode=test_mode)
        result = generator.generate_cfdi(sale)
        print(f"Generated invoice for sale {sale['_id']}")
        print(f"UUID: {result['uuid']}")
        print(f"Folio: {result['folio']}")
        print(f"XML Sample: {result['xml'][:200]}...")  # Show first 200 chars of XML
        
        # Mark sale as invoiced
        Sale.update_sale(
            db=db,
            sale_id=sale['_id'],
            is_invoiced=True,
            invoice_uuid=result['uuid'],
            invoice_date=datetime.now()
        )
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
    
    print("-" * 50)

def test_global_invoice(test_mode=True):
    """Test generating global invoice"""
    print(f"\nTesting Global Invoice Generation (Mode: {'Test' if test_mode else 'Production'}):")
    print("-" * 50)
    
    db = get_db()
    # Get all uninvoiced sales
    sales = Sale.get_uninvoiced_sales(db)
    print(f"Found {len(sales)} pending sales for global invoice")
    
    if not sales:
        print("No uninvoiced sales found")
        return
    
    try:
        generator = CFDIGenerator(test_mode=test_mode)
        result = generator.generate_global_cfdi(sales, datetime.now())
        print(f"Generated global invoice for {len(sales)} sales")
        print(f"UUID: {result['uuid']}")
        print(f"Folio: {result['folio']}")
        print(f"XML Sample: {result['xml'][:200]}...")  # Show first 200 chars of XML
        
        # Mark sales as invoiced
        for sale in sales:
            Sale.update_sale(
                db=db,
                sale_id=sale['_id'],
                is_invoiced=True,
                invoice_uuid=result['uuid'],
                invoice_date=datetime.now()
            )
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
    
    print("-" * 50)

def main():
    """Main test function"""
    print("Starting POS System Test")
    print("=" * 50)
    print("\nCreating Test Sales:")
    print("-" * 50)
    
    app = create_app('default')
    with app.app_context():
        # Create test data
        create_test_products()
        create_test_sales()
        
        # Test invoice generation in test mode only
        test_individual_invoice(test_mode=True)
        test_global_invoice(test_mode=True)
    
    print("\nTest Complete!")

if __name__ == "__main__":
    main()

import unittest
from api import app
import json

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_get_ventas(self):
        response = self.app.get('/api/ventas')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)

    def test_create_venta(self):
        venta_data = {
            "timestamp": "2025-03-18T10:00:00",
            "amount": 100.0,
            "payment_method": "cash",
            "client_id": "some_client_id",
            "products": []
        }
        response = self.app.post('/api/ventas', data=json.dumps(venta_data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.json)

    def test_get_cfdi(self):
        response = self.app.get('/api/cfdi')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)

    def test_create_cfdi(self):
        cfdi_data = {
            "emisor": {"nombre": "Emisor", "rfc": "XAXX010101000"},
            "receptor": {"nombre": "Receptor", "rfc": "XEXX010101000"},
            "fecha": "2025-03-18T10:00:00",
            "total": 100.0,
            "uuid": "some-uuid",
            "xml": "<xml></xml>"
        }
        response = self.app.post('/api/cfdi', data=json.dumps(cfdi_data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.json)

    def test_get_nominas(self):
        response = self.app.get('/api/nominas')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)

    def test_create_nomina(self):
        nomina_data = {
            "empleado": {"nombre": "Empleado", "rfc": "XAXX010101000"},
            "fecha_pago": "2025-03-18T10:00:00",
            "percepciones": 1000.0,
            "deducciones": 200.0,
            "total": 800.0
        }
        response = self.app.post('/api/nominas', data=json.dumps(nomina_data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.json)

if __name__ == '__main__':
    unittest.main()
