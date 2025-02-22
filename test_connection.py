from convertir_ventas import create_app
from datetime import datetime

def test_mongodb_connection():
    try:
        app = create_app()
        with app.app_context():
            is_connected = app.db.client.server_info()['ok'] == 1.0
            print('MongoDB connection successful:', is_connected)
            
            # Test if we can access the clients collection
            client_count = app.db.clients.count_documents({})
            print('Number of clients in database:', client_count)
            
            # Test if default client exists, create if it doesn't
            default_client = app.db.clients.find_one({"name": "Cliente General"})
            if not default_client:
                print('Creating default client...')
                result = app.db.clients.insert_one({
                    "name": "Cliente General",
                    "rfc": "XAXX010101000",
                    "created_at": datetime.now()
                })
                default_client = app.db.clients.find_one({"_id": result.inserted_id})
                
            print('Default client exists:', default_client is not None)
            
    except Exception as e:
        print('Error:', str(e))

if __name__ == '__main__':
    test_mongodb_connection()
