import unittest
from crud_sales import app
from pymongo import MongoClient
import os

class TestCrudSales(unittest.TestCase):
    def setUp(self):
        # Set up the Flask test client
        self.app = app.test_client()
        self.app.testing = True

        # Set up MongoDB client
        mongodb_uri = os.getenv('MONGODB_URI')
        self.client = MongoClient(mongodb_uri)
        self.db = self.client['pos_db']

        # Insert a test sale
        self.test_sale = {
            "client_id": "60d5ec49f1d2a2a5d4e8b456",
            "total_amount": 100.0,
            "amount_received": 120.0,
            "change_amount": 20.0,
            "details": [
                {"product_id": "60d5ec49f1d2a2a5d4e8b457", "quantity": 2, "price": 50.0}
            ],
            "is_invoiced": False,
            "invoice_uuid": None,
            "invoice_date": None,
            "created_at": "2025-03-21T10:25:56",
            "updated_at": "2025-03-21T10:25:56",
            "global_invoice_id": None
        }
        self.sale_id = self.db.sales.insert_one(self.test_sale).inserted_id

    def tearDown(self):
        # Clean up the database
        self.db.sales.delete_many({})
        self.client.close()

    def test_create_sale(self):
        # Test data
        test_data = {
            "client_id": "60d5ec49f1d2a2a5d4e8b456",
            "total_amount": 100.0,
            "amount_received": 120.0,
            "change_amount": 20.0,
            "details": [
                {"product_id": "60d5ec49f1d2a2a5d4e8b457", "quantity": 2, "price": 50.0}
            ]
        }

        # Send POST request to the endpoint
        response = self.app.post('/api/sales', json=test_data)

        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertIn('_id', response.json)

    def test_get_sales(self):
        # Send GET request to the endpoint
        response = self.app.get('/api/sales')

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)

    def test_get_sale(self):
        # Use the inserted sale's ObjectId for testing
        response = self.app.get(f'/api/sales/{str(self.sale_id)}')

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, dict)

    def test_update_sale(self):
        # Test data
        test_data = {
            "total_amount": 150.0,
            "amount_received": 170.0,
            "change_amount": 20.0,
            "details": [
                {"product_id": "60d5ec49f1d2a2a5d4e8b457", "quantity": 3, "price": 50.0}
            ]
        }

        # Send PUT request to the endpoint
        response = self.app.put(f'/api/sales/{str(self.sale_id)}', json=test_data)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'Sale updated')

    def test_delete_sale(self):
        # Send DELETE request to the endpoint
        response = self.app.delete(f'/api/sales/{str(self.sale_id)}')

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'Sale deleted')

if __name__ == '__main__':
    unittest.main()
