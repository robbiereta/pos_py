import pytest
from datetime import datetime
import json

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert data['database'] == 'connected'

def test_create_sale(client, test_db_session):
    """Test sale creation endpoint"""
    sale_data = {
        "total_amount": 15299.99,
        "products": [
            {
                "id": 1,
                "name": "Test Laptop",
                "price": 15000.0,
                "quantity": 1
            },
            {
                "id": 2,
                "name": "Test Mouse",
                "price": 299.99,
                "quantity": 1
            }
        ]
    }
    
    response = client.post('/sale',
                         data=json.dumps(sale_data),
                         content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'sale_id' in data

def test_create_sale_with_invoice(client, test_db_session):
    """Test sale creation with invoice generation"""
    sale_data = {
        "total_amount": 15299.99,
        "products": [
            {
                "id": 1,
                "name": "Test Laptop",
                "price": 15000.0,
                "quantity": 1
            }
        ],
        "generate_invoice": True
    }
    
    response = client.post('/sale',
                         data=json.dumps(sale_data),
                         content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'sale_id' in data
    assert 'cfdi_invoice' in data
    assert 'uuid' in data['cfdi_invoice']
    assert 'xml' in data['cfdi_invoice']

def test_get_pending_sales(client, test_db_session, test_sale):
    """Test getting pending sales"""
    response = client.get('/global-invoice/pending-sales')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]['total_amount'] == 15299.99

def test_generate_global_invoice(client, test_db_session, test_sale):
    """Test global invoice generation"""
    invoice_data = {
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    
    response = client.post('/global-invoice/generate',
                         data=json.dumps(invoice_data),
                         content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'cfdi_uuid' in data
    assert 'xml_content' in data
