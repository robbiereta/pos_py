import pandas as pd
from pymongo import MongoClient
from datetime import datetime

def import_categories_from_csv(file_path):
    """Import categories from CSV file"""
    print(f"\nImporting categories from {file_path}")
    print("=" * 50)
    
    # Read CSV file
    df = pd.read_csv(file_path)
    
    # Initialize MongoDB connection
    client = MongoClient('mongodb://localhost:27017/')
    db = client.pos_system
    
    # Initialize counters
    created = 0
    updated = 0
    errors = 0
    
    # Process each row
    for index, row in df.iterrows():
        try:
            # Clean and prepare data
            sku = str(row['MOTACE']).strip()
            name = str(row['ACEITE']).strip()
            
            if not name:
                print(f"Skipping row {index + 2}: Missing product name")
                errors += 1
                continue
            
            # Extract category from the SKU (first 3 letters)
            category_name = sku[:3] if sku else None
            if not category_name:
                print(f"Skipping row {index + 2}: Cannot extract category")
                errors += 1
                continue
            
            # Check if category exists
            existing_category = db.categories.find_one({"name": category_name})
            
            if existing_category:
                updated += 1
                print(f"Category already exists: {category_name}")
            else:
                # Create new category
                category = {
                    "name": category_name,
                    "description": f"Category for {category_name} products",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                db.categories.insert_one(category)
                created += 1
                print(f"Created category: {category_name}")
                
        except Exception as e:
            print(f"Error in row {index + 2}: {str(e)}")
            errors += 1
    
    # Print summary
    print("\nImport Summary:")
    print("-" * 50)
    print(f"Categories created: {created}")
    print(f"Categories already exist: {updated}")
    print(f"Errors: {errors}")
    print(f"Total rows processed: {len(df)}")

def assign_categories_to_products():
    """Assign categories to products"""
    print("\nAssigning categories to products")
    print("=" * 50)
    
    # Initialize MongoDB connection
    client = MongoClient('mongodb://localhost:27017/')
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
    # Import categories
    import_categories_from_csv('prods.csv')
    
    # Assign categories to products
    assign_categories_to_products()

if __name__ == "__main__":
    main()
