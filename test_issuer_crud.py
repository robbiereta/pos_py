import unittest
from issuer_crud import app

class TestIssuerCrud(unittest.TestCase):
    def setUp(self):
        # Set up the Flask test client
        self.app = app.test_client()
        self.app.testing = True

    def test_create_emitter(self):
        # Test data
        test_data = {
            "nombre": "Test Name",
            "rfc": "RFC123456789",
            "regimenFiscal": "Regimen Fiscal",
            "domicilioFiscal": "Test Address",
            "telefono": "1234567890",
            "correoElectronico": "test@example.com"
        }

        # Send POST request to the endpoint
        response = self.app.post('/api/emisores', json=test_data)

        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.json)

    def test_get_emisores(self):
        # Send GET request to the endpoint
        response = self.app.get('/api/emisores')

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)

    def test_get_emitter(self):
        # Send GET request to the endpoint
        response = self.app.get('/api/emisores/1')

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, dict)      

    def test_update_emitter(self):
        # Test data
        test_data = {
            "nombre": "Updated Name",
            "rfc": "RFC123456789",
            "regimenFiscal": "Updated Regimen Fiscal",
            "domicilioFiscal": "Updated Address",
            "telefono": "1234567890",
            "correoElectronico": "updated@example.com"
        }

        # Send PUT request to the endpoint
        response = self.app.put('/api/emisores/1', json=test_data)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'Emitter updated')

    def test_delete_emitter(self):
        # Send DELETE request to the endpoint
        response = self.app.delete('/api/emisores/1')

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'Emitter deleted')

if __name__ == '__main__':
    unittest.main()
