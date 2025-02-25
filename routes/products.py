from flask import Blueprint, jsonify, request, current_app
from bson import ObjectId
from datetime import datetime
from db import get_db
import logging
import sqlite3
import os

bp = Blueprint('products', __name__)

def get_sqlite_connection():
    """Get SQLite connection"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pos.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Create products table if it doesn't exist
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        sku TEXT,
        price REAL DEFAULT 0,
        description TEXT,
        stock INTEGER DEFAULT 0,
        track_stock BOOLEAN DEFAULT 1,
        image_url TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    ''')
    
    # Check if track_stock column exists and add it if it doesn't
    cursor.execute("PRAGMA table_info(products)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'track_stock' not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN track_stock BOOLEAN DEFAULT 1")
        
    conn.commit()
    return conn

@bp.route('/api/products', methods=['GET'])
def get_products():
    """Get all products"""
    try:
        # Always try SQLite first
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            
            search_query = request.args.get('q', '').strip()
            
            if search_query:
                query = "SELECT * FROM products WHERE name LIKE ? OR sku LIKE ? ORDER BY name"
                cursor.execute(query, (f'%{search_query}%', f'%{search_query}%'))
            else:
                query = "SELECT * FROM products ORDER BY name"
                cursor.execute(query)
                
            products = []
            for row in cursor.fetchall():
                product = dict(row)
                # Convert id to _id for consistent API
                product['_id'] = str(product['id'])
                products.append(product)
                
            conn.close()
            
            current_app.logger.info(f"Retrieved {len(products)} products from SQLite")
            return jsonify(products)
            
        except Exception as e:
            current_app.logger.warning(f"Error getting products from SQLite: {e}. Trying MongoDB...")
            
            # Fallback to MongoDB
            db = get_db()
            if not db:
                return jsonify({"error": "Database connection failed"}), 500
                
            search_query = request.args.get('q', '').strip()
            
            # Build query
            query = {}
            if search_query:
                query['$or'] = [
                    {'name': {'$regex': search_query, '$options': 'i'}},
                    {'sku': {'$regex': search_query, '$options': 'i'}}
                ]
            
            # Get products and sort by name
            products = list(db.products.find(query).sort('name', 1))
            
            # Convert ObjectId to string for JSON serialization
            for product in products:
                product['_id'] = str(product['_id'])
            
            current_app.logger.info(f"Retrieved {len(products)} products from MongoDB")
            return jsonify(products)
                
    except Exception as e:
        logging.error(f"Error in get_products: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@bp.route('/api/products', methods=['POST'])
def create_product():
    """Create a new product"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Product name is required'}), 400
            
        # Try SQLite first
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            
            # Check if product with same name exists
            cursor.execute("SELECT id FROM products WHERE name = ?", (data['name'],))
            if cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Product with this name already exists'}), 400
            
            # Insert product
            now = datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO products (name, sku, price, description, stock, track_stock, image_url, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    data['name'],
                    data.get('sku', ''),
                    float(data.get('price', 0)),
                    data.get('description', ''),
                    int(data.get('stock', 0)),
                    bool(data.get('track_stock', True)),
                    data.get('image_url', ''),
                    now,
                    now
                )
            )
            conn.commit()
            
            # Get the inserted product
            product_id = cursor.lastrowid
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            product = dict(cursor.fetchone())
            product['_id'] = str(product['id'])
            
            conn.close()
            
            current_app.logger.info(f"Created product in SQLite: {data['name']}")
            return jsonify(product), 201
            
        except Exception as e:
            current_app.logger.warning(f"Error creating product in SQLite: {e}. Trying MongoDB...")
            
            # Fallback to MongoDB
            db = get_db()
            if not db:
                return jsonify({"error": "Database connection failed"}), 500
                
            # Check if product with same name exists
            if db.products.find_one({'name': data['name']}):
                return jsonify({'error': 'Product with this name already exists'}), 400
            
            # Prepare product data
            product = {
                'name': data['name'],
                'sku': data.get('sku', ''),
                'price': float(data.get('price', 0)),
                'description': data.get('description', ''),
                'stock': int(data.get('stock', 0)),
                'track_stock': bool(data.get('track_stock', True)),
                'image_url': data.get('image_url', ''),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Insert product
            result = db.products.insert_one(product)
            product['_id'] = str(result.inserted_id)
            
            current_app.logger.info(f"Created product in MongoDB: {data['name']}")
            return jsonify(product), 201
            
    except Exception as e:
        logging.error(f"Error in create_product: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@bp.route('/api/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Product name is required'}), 400
            
        # Try SQLite first
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            
            # Check if product exists
            cursor.execute("SELECT id FROM products WHERE id = ?", (product_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Product not found'}), 404
                
            # Check if product with same name exists (excluding current product)
            cursor.execute("SELECT id FROM products WHERE name = ? AND id != ?", 
                          (data['name'], product_id))
            if cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Product with this name already exists'}), 400
            
            # Update product
            now = datetime.utcnow().isoformat()
            cursor.execute(
                """UPDATE products SET 
                   name = ?, 
                   sku = ?, 
                   price = ?,
                   description = ?,
                   stock = ?,
                   track_stock = ?,
                   image_url = ?,
                   updated_at = ? 
                   WHERE id = ?""",
                (
                    data['name'],
                    data.get('sku', ''),
                    float(data.get('price', 0)),
                    data.get('description', ''),
                    int(data.get('stock', 0)),
                    bool(data.get('track_stock', True)),
                    data.get('image_url', ''),
                    now,
                    product_id
                )
            )
            conn.commit()
            
            # Get the updated product
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            product = dict(cursor.fetchone())
            product['_id'] = str(product['id'])
            
            conn.close()
            
            current_app.logger.info(f"Updated product in SQLite: {data['name']}")
            return jsonify(product)
            
        except Exception as e:
            current_app.logger.warning(f"Error updating product in SQLite: {e}. Trying MongoDB...")
            
            # Fallback to MongoDB
            db = get_db()
            if not db:
                return jsonify({"error": "Database connection failed"}), 500
                
            # Check if product with same name exists (excluding current product)
            try:
                obj_id = ObjectId(product_id)
            except:
                return jsonify({'error': 'Invalid product ID'}), 400
                
            existing = db.products.find_one({
                'name': data['name'],
                '_id': {'$ne': obj_id}
            })
            if existing:
                return jsonify({'error': 'Product with this name already exists'}), 400
            
            # Prepare update data
            update_data = {
                'name': data['name'],
                'sku': data.get('sku', ''),
                'price': float(data.get('price', 0)),
                'description': data.get('description', ''),
                'stock': int(data.get('stock', 0)),
                'track_stock': bool(data.get('track_stock', True)),
                'image_url': data.get('image_url', ''),
                'updated_at': datetime.utcnow()
            }
            
            # Update product
            result = db.products.update_one(
                {'_id': obj_id},
                {'$set': update_data}
            )
            
            if result.modified_count == 0:
                return jsonify({'error': 'Product not found'}), 404
                
            # Get updated product
            product = db.products.find_one({'_id': obj_id})
            product['_id'] = str(product['_id'])
            
            current_app.logger.info(f"Updated product in MongoDB: {data['name']}")
            return jsonify(product)
            
    except Exception as e:
        logging.error(f"Error in update_product: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@bp.route('/api/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    try:
        # Try SQLite first
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            
            # Check if product exists
            cursor.execute("SELECT id FROM products WHERE id = ?", (product_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Product not found'}), 404
                
            # Delete product
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            conn.close()
            
            current_app.logger.info(f"Deleted product from SQLite, ID: {product_id}")
            return jsonify({'message': 'Product deleted successfully'})
            
        except Exception as e:
            current_app.logger.warning(f"Error deleting product from SQLite: {e}. Trying MongoDB...")
            
            # Fallback to MongoDB
            db = get_db()
            if not db:
                return jsonify({"error": "Database connection failed"}), 500
                
            try:
                obj_id = ObjectId(product_id)
            except:
                return jsonify({'error': 'Invalid product ID'}), 400
                
            result = db.products.delete_one({'_id': obj_id})
            
            if result.deleted_count == 0:
                return jsonify({'error': 'Product not found'}), 404
                
            current_app.logger.info(f"Deleted product from MongoDB, ID: {product_id}")
            return jsonify({'message': 'Product deleted successfully'})
            
    except Exception as e:
        logging.error(f"Error in delete_product: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
