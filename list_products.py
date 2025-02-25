import os
from dotenv import load_dotenv
from pymongo import MongoClient
from tabulate import tabulate

# Load environment variables
load_dotenv()

def get_db():
    """Get MongoDB database instance"""
    client = MongoClient(os.getenv('MONGODB_URI'))
    return client.pos_system

def list_products():
    """List all products in the database"""
    db = get_db()
    
    # Get all products and sort by name
    products = list(db.products.find().sort("name", 1))
    
    if not products:
        print("No products found in database.")
        return
        
    # Prepare data for tabulate
    headers = ["Name", "SKU", "Price"]
    rows = [[p["name"], p.get("sku", "N/A"), f"${p.get('price', 0.0):.2f}"] for p in products]
    
    # Print table
    print("\nProducts List")
    print("=" * 50)
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print(f"\nTotal Products: {len(products)}")

if __name__ == "__main__":
    list_products()
