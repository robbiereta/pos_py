import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from models import Product

# Load environment variables
load_dotenv()

def get_db():
    """Get MongoDB database instance"""
    client = MongoClient(os.getenv('MONGODB_URI'))
    return client.pos_system

def import_products_from_excel(file_path):
    """Import products from Excel file"""
    print(f"\nImporting products from {file_path}")
    print("=" * 50)
    
    # Read Excel file
    df = pd.read_excel(file_path)
    
    # Initialize counters
    created = 0
    updated = 0
    errors = 0
    
    # Get database connection
    db = get_db()
    
    # Process each row
    for index, row in df.iterrows():
        try:
            # Clean and prepare data
            sku = str(row['CODIGO']).strip() if pd.notna(row['CODIGO']) else None
            name = str(row['PRODUCTO']).strip() if pd.notna(row['PRODUCTO']) else None
            price = float(row['P. VENTA ']) if pd.notna(row['P. VENTA ']) else 0.0
            
            if not name or name == 'PRODUCTO':
                print(f"Skipping row {index + 2}: Missing product name")
                errors += 1
                continue
                
            # Check if product exists
            existing_product = db.products.find_one({"name": name})
            
            if existing_product:
                # Update existing product
                db.products.update_one(
                    {"_id": existing_product['_id']},
                    {
                        "$set": {
                            "price": price,
                            "sku": sku,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                updated += 1
                print(f"Updated product: {name}")
            else:
                # Create new product
                db.products.insert_one({
                    "name": name,
                    "price": price,
                    "sku": sku,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                created += 1
                print(f"Created product: {name}")
                
        except KeyError as e:
            print(f"Error in row {index + 2}: {str(e)}")
            errors += 1
            continue
        except Exception as e:
            print(f"Error in row {index + 2}: {str(e)}")
            errors += 1
            continue
    
    print("\nImport Summary:")
    print("-" * 50)
    print(f"Products created: {created}")
    print(f"Products updated: {updated}")
    print(f"Errors: {errors}")
    print(f"Total rows processed: {len(df)}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python import_products.py <excel_file>")
        sys.exit(1)
    import_products_from_excel(sys.argv[1])

if __name__ == "__main__":
    import sys
    main()
