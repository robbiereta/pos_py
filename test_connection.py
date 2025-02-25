from app import create_app
from db import get_db
from datetime import datetime

def test_mongodb_connection():
    try:
        app = create_app()
        with app.app_context():
            db = get_db()
            if not db:
                print('ERROR: Database connection failed')
                return

            # Test if connection is valid
            try:
                is_connected = db.client.server_info()['ok'] == 1.0
                print('MongoDB connection successful:', is_connected)
            except Exception as e:
                print('ERROR connecting to MongoDB:', str(e))
                return
            
            # Test if we can access the clients collection
            try:
                client_count = db.clients.count_documents({})
                print('Number of clients in database:', client_count)
            except Exception as e:
                print('ERROR accessing clients collection:', str(e))
                return
            
            # Test if default client exists
            try:
                default_client = db.clients.find_one({"name": "Cliente General"})
                print('Default client exists:', default_client is not None)
            except Exception as e:
                print('ERROR accessing default client:', str(e))
                return
            
    except Exception as e:
        print('ERROR in test script:', str(e))

if __name__ == '__main__':
    test_mongodb_connection()
