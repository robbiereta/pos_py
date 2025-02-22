from convertir_ventas import create_app
from pprint import pprint

def check_sale_structure():
    try:
        app = create_app()
        with app.app_context():
            # Get one sale record
            sale = app.db.sales.find_one({})
            if sale:
                print("Sample sale record structure:")
                pprint(sale)
            else:
                print("No sales found in database")
            
            # Get collection names
            collections = app.db.list_collection_names()
            print("\nAvailable collections:")
            print(collections)
            
            # Count documents in each collection
            print("\nDocument counts:")
            for collection in collections:
                count = app.db.get_collection(collection).count_documents({})
                print(f"{collection}: {count} documents")
    
    except Exception as e:
        print('Error:', str(e))

if __name__ == '__main__':
    check_sale_structure()
