import unittest
from datetime import datetime, timedelta
import json
import os
from app import create_app
from models import db, Sale, Product, GlobalInvoice

class POSSystemTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        if os.path.exists('test.db'):
            os.remove('test.db')

    def test_product_creation(self):
        """Test product creation"""
        response = self.client.post('/products', json={
            'name': 'Test Product',
            'price': 100.0,
            'stock': 10
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'Test Product')
        self.assertEqual(data['price'], 100.0)
        self.assertEqual(data['stock'], 10)

    def test_get_products(self):
        """Test getting all products"""
        # Create test product
        product = Product(name='Test Product', price=100.0, stock=10)
        db.session.add(product)
        db.session.commit()

        response = self.client.get('/products')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Product')

    def test_create_sale(self):
        """Test sale creation"""
        # Create test product first
        product = Product(name='Test Product', price=100.0, stock=10)
        db.session.add(product)
        db.session.commit()

        response = self.client.post('/sales', json={
            'total_amount': 200.0,
            'products': [
                {'id': product.id, 'quantity': 2, 'price': 100.0}
            ]
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['total_amount'], 200.0)

    def test_daily_summary(self):
        """Test daily summary generation"""
        # Create test sales for today
        product = Product(name='Test Product', price=100.0, stock=10)
        db.session.add(product)
        db.session.commit()

        for _ in range(3):
            sale = Sale(
                total_amount=200.0,
                products=[{'id': product.id, 'quantity': 2, 'price': 100.0}]
            )
            db.session.add(sale)
        db.session.commit()

        response = self.client.get('/daily_summary')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('total_sales', data)
        self.assertIn('total_amount', data)
        self.assertEqual(data['total_sales'], 3)
        self.assertEqual(data['total_amount'], 600.0)

    def test_global_invoice_generation(self):
        """Test global invoice generation"""
        # Create test sales
        product = Product(name='Test Product', price=100.0, stock=10)
        db.session.add(product)
        db.session.commit()

        # Create some sales
        for _ in range(3):
            sale = Sale(
                total_amount=200.0,
                products=[{'id': product.id, 'quantity': 2, 'price': 100.0}]
            )
            db.session.add(sale)
        db.session.commit()

        # Test global invoice generation
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now() + timedelta(days=1)

        response = self.client.post('/generate_global_invoice', json={
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'generate': True
        })

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('invoice_data', data)
        self.assertEqual(data['invoice_data']['total_ventas'], 3)

    def test_global_invoice_no_sales(self):
        """Test global invoice generation with no sales"""
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now() + timedelta(days=1)
        
        response = self.client.post('/generate_global_invoice', json={
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'generate': True
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_invalid_product_creation(self):
        """Test invalid product creation"""
        response = self.client.post('/products', json={
            'name': 'Test Product'  # Missing required price
        })
        self.assertEqual(response.status_code, 400)

    def test_invalid_sale_creation(self):
        """Test invalid sale creation"""
        response = self.client.post('/sales', json={
            'products': []  # Missing required total_amount
        })
        self.assertEqual(response.status_code, 400)

    def test_product_stock_update(self):
        """Test product stock update"""
        # Create test product
        product = Product(name='Test Product', price=100.0, stock=10)
        db.session.add(product)
        db.session.commit()

        # Create a sale that should reduce stock
        response = self.client.post('/sales', json={
            'total_amount': 200.0,
            'products': [
                {'id': product.id, 'quantity': 2, 'price': 100.0}
            ]
        })
        
        # Verify stock was reduced
        updated_product = Product.query.get(product.id)
        self.assertEqual(updated_product.stock, 8)

if __name__ == '__main__':
    unittest.main()
