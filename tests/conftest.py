import pytest
from app import create_app, db
from models import Product, Sale
import os
from sqlalchemy.orm import scoped_session, sessionmaker

@pytest.fixture
def app():
    """Create and configure a test Flask application instance"""
    app = create_app('testing')
    
    # Create test database and tables
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner"""
    return app.test_cli_runner()

@pytest.fixture
def test_db_session(app):
    """Create a test database session"""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Create a scoped session
        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)
        
        # Override the default session with our test session
        db.session = session
        
        # Add test products
        products = [
            Product(name="Test Laptop", price=15000.0),
            Product(name="Test Mouse", price=299.99)
        ]
        for product in products:
            session.add(product)
        session.commit()
        
        yield session
        
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture
def test_sale(test_db_session):
    """Create a test sale"""
    sale = Sale(
        total_amount=15299.99,
        products=[
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
    )
    test_db_session.add(sale)
    test_db_session.commit()
    return sale
