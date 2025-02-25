from flask import Blueprint, jsonify, request
from bson import ObjectId
from datetime import datetime
from db import get_db

bp = Blueprint('products', __name__)

@bp.route('/api/products', methods=['GET'])
def get_products():
    """Get all products"""
    db = get_db()
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
    
    return jsonify(products)

@bp.route('/api/products', methods=['POST'])
def create_product():
    """Create a new product"""
    db = get_db()
    data = request.json
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({'error': 'Product name is required'}), 400
        
    # Check if product with same name exists
    if db.products.find_one({'name': data['name']}):
        return jsonify({'error': 'Product with this name already exists'}), 400
    
    # Prepare product data
    product = {
        'name': data['name'],
        'sku': data.get('sku'),
        'price': float(data.get('price', 0)),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    # Insert product
    result = db.products.insert_one(product)
    product['_id'] = str(result.inserted_id)
    
    return jsonify(product), 201

@bp.route('/api/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product"""
    db = get_db()
    data = request.json
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({'error': 'Product name is required'}), 400
        
    # Check if product with same name exists (excluding current product)
    existing = db.products.find_one({
        'name': data['name'],
        '_id': {'$ne': ObjectId(product_id)}
    })
    if existing:
        return jsonify({'error': 'Product with this name already exists'}), 400
    
    # Prepare update data
    update_data = {
        'name': data['name'],
        'sku': data.get('sku'),
        'price': float(data.get('price', 0)),
        'updated_at': datetime.utcnow()
    }
    
    # Update product
    result = db.products.update_one(
        {'_id': ObjectId(product_id)},
        {'$set': update_data}
    )
    
    if result.matched_count == 0:
        return jsonify({'error': 'Product not found'}), 404
        
    # Get updated product
    product = db.products.find_one({'_id': ObjectId(product_id)})
    product['_id'] = str(product['_id'])
    
    return jsonify(product)

@bp.route('/api/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    db = get_db()
    
    # Check if product exists
    product = db.products.find_one({'_id': ObjectId(product_id)})
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Delete product
    db.products.delete_one({'_id': ObjectId(product_id)})
    
    return jsonify({'message': 'Product deleted successfully'})
