from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from models import Product, Category
from db import get_db
from bson import ObjectId
from datetime import datetime

products_bp = Blueprint('products', __name__)

@products_bp.route('/products')
def list_products():
    db = get_db()
    products = list(db.products.find())
    categories = list(db.categories.find())
    
    # Convert ObjectId to string for JSON serialization
    for product in products:
        product['_id'] = str(product['_id'])
        if product.get('category_id'):
            product['category_id'] = str(product['category_id'])
            # Add category name
            category = next((c for c in categories if str(c['_id']) == product['category_id']), None)
            product['category_name'] = category['name'] if category else None
    
    return render_template('products.html', products=products, categories=categories)

@products_bp.route('/api/products', methods=['GET'])
def get_products():
    db = get_db()
    products = list(db.products.find())
    
    # Convert ObjectId to string for JSON serialization
    for product in products:
        product['_id'] = str(product['_id'])
        if product.get('category_id'):
            product['category_id'] = str(product['category_id'])
    
    return jsonify(products)

@products_bp.route('/api/products', methods=['POST'])
def create_product():
    db = get_db()
    data = request.json
    
    try:
        # Convert category_id to ObjectId if present
        if data.get('category_id'):
            data['category_id'] = ObjectId(data['category_id'])
        
        # Create product
        product = Product.create_product(
            db,
            name=data['name'],
            price=float(data['price']),
            stock=int(data.get('stock', 0)),
            description=data.get('description'),
            sku=data.get('sku'),
            image_url=data.get('image_url'),
            min_stock=int(data.get('min_stock', 0)),
            sat_code=data.get('sat_code'),
            category_id=data.get('category_id')
        )
        
        # Convert ObjectId to string for response
        product['_id'] = str(product['_id'])
        if product.get('category_id'):
            product['category_id'] = str(product['category_id'])
        
        return jsonify({'success': True, 'product': product})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@products_bp.route('/api/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    db = get_db()
    data = request.json
    
    try:
        # Convert category_id to ObjectId if present
        if data.get('category_id'):
            data['category_id'] = ObjectId(data['category_id'])
        
        # Add updated_at timestamp
        data['updated_at'] = datetime.utcnow()
        
        # Update product
        result = db.products.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': data}
        )
        
        if result.modified_count > 0:
            # Get updated product
            product = db.products.find_one({'_id': ObjectId(product_id)})
            # Convert ObjectId to string
            product['_id'] = str(product['_id'])
            if product.get('category_id'):
                product['category_id'] = str(product['category_id'])
            return jsonify({'success': True, 'product': product})
        else:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@products_bp.route('/api/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    db = get_db()
    
    try:
        result = db.products.delete_one({'_id': ObjectId(product_id)})
        if result.deleted_count > 0:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
