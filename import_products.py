import pandas as pd
from app import create_app
from db import init_db, get_db
from models import Product
from datetime import datetime

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
            sku = str(row['MOTACE']).strip()
            name = str(row['ACEITE']).strip()
            price = float(row[25]) if pd.notna(row[25]) else 0.0
            sat_code = str(row[15121500]).strip() if pd.notna(row[15121500]) else None
            
            if not name or name == 'ACEITE':
                print(f"Skipping row {index + 2}: Missing product name")
                errors += 1
                continue
                
            # Check if product exists
            existing_product = db.products.find_one({"name": name})
            
            if existing_product:
                # Update existing product
                Product.update_product(
                    db=db,
                    product_id=existing_product['_id'],
                    price=price,
                    sku=sku,
                    sat_code=sat_code,
                    updated_at=datetime.utcnow()
                )
                updated += 1
                print(f"Updated product: {name}")
            else:
                # Create new product
                Product.create_product(
                    db=db,
                    name=name,
                    price=price,
                    sku=sku,
                    sat_code=sat_code,
                    stock=0,
                    min_stock=0
                )
                created += 1
                print(f"Created product: {name}")
                
        except Exception as e:
            print(f"Error in row {index + 2}: {str(e)}")
            errors += 1
    
    # Print summary
    print("\nImport Summary:")
    print("-" * 50)
    print(f"Products created: {created}")
    print(f"Products updated: {updated}")
    print(f"Errors: {errors}")
    print(f"Total rows processed: {len(df)}")

def main():
    """Main function"""
    app = create_app('default')
    with app.app_context():
        init_db(app)  # Initialize database with app instance
        import_products_from_excel('prods.xlsx')

if __name__ == "__main__":
    main()
