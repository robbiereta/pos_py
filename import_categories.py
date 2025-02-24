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
            sat_code = str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else ''
            
            if not name:
                print(f"Skipping row {index + 2}: Missing category name")
                errors += 1
                continue
                
            # Check if category exists by code
            existing_category = db.categories.find_one({"code": code})
            
            category_data = {
                "code": code,
                "name": name,
                "name_lower": name.lower(),  # Add lowercase name for better matching
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

def normalize_text(text):
    """Normalize text for better matching"""
    # Convert to lowercase
    text = text.lower()
    
    # Common word variations
    replacements = {
        'sproket': 'sprock',
        'sprocket': 'sprock',
        'rayos': 'rayo',
        'espejos': 'espejo',
        'puños': 'puño',
        'pedales': 'pedal',
        'direccionales': 'direccional',
        'claxon85': 'claxon moto',  # Handle specific SKU
        'claxon': 'claxon moto',  # Changed to exact match
        'manubrio': 'manubrio de motocicleta',  # Changed to exact match
        'tubo mobil': 'tubo',  # Added for TUBO MOBIL
    }
    
    # Apply replacements in reverse length order (longer matches first)
    sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)
    
    # Apply replacements
    for old, new in sorted_replacements:
        if old in text:  # Only replace if word is found
            # Ensure we're replacing whole words
            text = ' ' + text + ' '
            text = text.replace(' ' + old + ' ', ' ' + new + ' ')
            text = text.strip()
    
    return text

def get_word_tokens(text):
    """Get meaningful word tokens from text"""
    # Split into words and filter out common words
    stop_words = {'de', 'para', 'del', 'la', 'el', 'y', 'o', 'u', 'las', 'los', 'en'}
    words = text.split()
    return [w for w in words if w not in stop_words]

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
    
    # Get all categories for faster lookup
    categories = list(db.categories.find({}))
    
    # Create maps for category lookup
    category_map = {}  # Full name/code to category
    category_tokens = {}  # Word tokens to categories
    
    for cat in categories:
        # Add main name
        name = cat.get('name', '').lower()
        if name:
            normalized_name = normalize_text(name)
            category_map[normalized_name] = cat
            
            # Add word tokens
            for token in get_word_tokens(normalized_name):
                if token not in category_tokens:
                    category_tokens[token] = []
                category_tokens[token].append(cat)
        
        # Add code as alternative name
        code = cat.get('code', '').lower()
        if code:
            category_map[code] = cat
    
    # Initialize counters
    updated = 0
    errors = 0
    no_match = 0
    
    # Get all products
    products = db.products.find({})
    
    # Process each product
    for product in products:
        try:
            product_name = product.get('name', '').lower()
            if not product_name:
                continue
            
            # Normalize product name
            normalized_product = normalize_text(product_name)
            
            # Try to find a matching category
            matched_category = None
            max_match_score = 0
            
            # First try exact matches
            for cat_name, category in category_map.items():
                if cat_name in normalized_product and len(cat_name) > max_match_score:
                    matched_category = category
                    max_match_score = len(cat_name)
            
            # If no exact match, try token matching
            if not matched_category:
                product_tokens = get_word_tokens(normalized_product)
                token_matches = {}
                
                for token in product_tokens:
                    if token in category_tokens:
                        for cat in category_tokens[token]:
                            cat_id = str(cat['_id'])
                            if cat_id not in token_matches:
                                token_matches[cat_id] = {'category': cat, 'score': 0}
                            token_matches[cat_id]['score'] += 1
                
                # Find category with highest token match score
                for match_info in token_matches.values():
                    if match_info['score'] > max_match_score:
                        matched_category = match_info['category']
                        max_match_score = match_info['score']
            
            if not matched_category:
                print(f"No category match for product: {product.get('sku', '')} - {product.get('name', '')}")
                no_match += 1
                continue
            
            # Update product with category and SAT code
            update_data = {
                "category_id": matched_category["_id"],
                "category_name": matched_category["name"],
                "updated_at": datetime.utcnow()
            }
            
            # Only add SAT code if it exists
            if "sat_code" in matched_category and matched_category["sat_code"]:
                update_data["sat_code"] = matched_category["sat_code"]
            
            db.products.update_one(
                {"_id": product["_id"]},
                {"$set": update_data}
            )
            updated += 1
            print(f"Assigned category '{matched_category['name']}' to product: {product.get('name', '')}")
            if "sat_code" in matched_category:
                print(f"  SAT code: {matched_category['sat_code']}")
            
        except Exception as e:
            print(f"Error updating product {product.get('name', '')}: {str(e)}")
            errors += 1
    
    # Print summary
    print("\nAssignment Summary:")
    print("-" * 50)
    print(f"Products updated: {updated}")
    print(f"Products with no category match: {no_match}")
    print(f"Errors: {errors}")

def main():
    """Main function"""
    # Import categories from cat.csv
    import_categories_from_csv('cat.csv')
    
    # Assign categories to products
    assign_categories_to_products()

if __name__ == "__main__":
    main()
