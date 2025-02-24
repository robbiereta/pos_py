import pandas as pd
import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def import_categories_from_csv(file_path):
    """Import categories from CSV file"""
    print(f"\nImporting categories from {file_path}")
    print("=" * 50)
    
    # Read CSV file
    df = pd.read_csv(file_path)
    
    # Initialize MongoDB connection using environment variable
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        mongo_uri = 'mongodb://localhost:27017/'
        print("Warning: MONGODB_URI not found in environment, using default local connection")
    
    client = MongoClient(mongo_uri)
    db = client.pos_system
    
    # Initialize counters
    created = 0
    updated = 0
    errors = 0
    
    # Process each row
    for index, row in df.iterrows():
        try:
            # Clean and prepare data
            code = str(row['MOTACE']).strip()
            name = str(row['ACEITE']).strip()
            sat_code = str(row.iloc[3]).strip() if len(row) > 3 else ''
            
            if not name:
                print(f"Skipping row {index + 2}: Missing category name")
                errors += 1
                continue
                
            # Check if category exists by code
            existing_category = db.categories.find_one({"code": code})
            
            category_data = {
                "code": code,
                "name": name,
                "sat_code": sat_code,
                "updated_at": datetime.utcnow()
            }
            
            if existing_category:
                # Update existing category
                db.categories.update_one(
                    {"_id": existing_category["_id"]},
                    {"$set": category_data}
                )
                updated += 1
                print(f"Updated category: {code} - {name} (SAT: {sat_code})")
            else:
                # Create new category
                category_data["created_at"] = datetime.utcnow()
                db.categories.insert_one(category_data)
                created += 1
                print(f"Created category: {code} - {name} (SAT: {sat_code})")
                
        except Exception as e:
            print(f"Error in row {index + 2}: {str(e)}")
            errors += 1
    
    # Print summary
    print("\nImport Summary:")
    print("-" * 50)
    print(f"Categories created: {created}")
    print(f"Categories updated: {updated}")
    print(f"Errors: {errors}")
    print(f"Total rows processed: {len(df)}")

def assign_categories_to_products():
    """Assign categories to products"""
    print("\nAssigning categories to products")
    print("=" * 50)
    
    # Initialize MongoDB connection using environment variable
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        mongo_uri = 'mongodb://localhost:27017/'
        print("Warning: MONGODB_URI not found in environment, using default local connection")
    
    client = MongoClient(mongo_uri)
    db = client.pos_system
    
    # Initialize counters
    updated = 0
    errors = 0
    
    # Get all products
    products = db.products.find({})
    
    # Process each product
    for product in products:
        try:
            sku = product.get('sku', '')
            if not sku:
                continue
                
            # Extract category from the SKU (first 3 letters)
            category_name = sku[:3] if sku else None
            if not category_name:
                continue
            
            # Find category
            category = db.categories.find_one({"name": category_name})
            if not category:
                continue
            
            # Update product with category
            db.products.update_one(
                {"_id": product['_id']},
                {"$set": {
                    "category_id": category['_id'],
                    "updated_at": datetime.utcnow()
                }}
            )
            updated += 1
            print(f"Assigned category '{category_name}' to product: {product.get('name', '')}")
            
        except Exception as e:
            print(f"Error processing product {product.get('name', '')}: {str(e)}")
            errors += 1
    
    # Print summary
    print("\nAssignment Summary:")
    print("-" * 50)
    print(f"Products updated: {updated}")
    print(f"Errors: {errors}")

def main():
    """Main function"""
    # Import categories from cat.csv
    import_categories_from_csv('cat.csv')
    
    # Assign categories to products
    assign_categories_to_products()

if __name__ == "__main__":
    main()
