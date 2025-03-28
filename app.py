from flask import Flask, request, jsonify, render_template, make_response, send_file
from flask_cors import CORS
from datetime import datetime
from cfdi_generator import CFDIGenerator
from config import config
from db import init_db, get_db
import os
from dotenv import load_dotenv
import pandas as pd
from werkzeug.utils import secure_filename
import requests
from routes.export import export_bp
from routes.invoice_ocr import invoice_ocr_bp
from routes.products import products_bp
import pytesseract
from PIL import Image
import io
from bson import ObjectId
from pymongo import MongoClient
import unittest

# Load environment variables
load_dotenv()

# Create the Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load configuration
app.config.from_object(config['default'])

# Initialize MongoDB
mongo = init_db(app)
app.db = mongo.db  # Add db instance to app context

# Import models
from models import Sale, Product, Client, GlobalInvoice

# Register blueprints
from routes.clients import clients_bp
app.register_blueprint(clients_bp)
app.register_blueprint(export_bp)
app.register_blueprint(invoice_ocr_bp)
app.register_blueprint(products_bp)

# Configuration for image uploads
UPLOAD_FOLDER = 'static/remisiones'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_remision_image(image_path):
    try:
        # Configure Tesseract path
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Open and process the image
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='spa')
        
        # Process the extracted text
        lines = text.split('\n')
        items = []
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.split()
            if len(parts) >= 4:
                try:
                    # Find the index of Pza/Par/Pllo/Kit
                    unit_index = -1
                    for i, part in enumerate(parts):
                        if part in ['Pza', 'Par', 'Pllo', 'Kit']:
                            unit_index = i
                            break
                    
                    if unit_index > 0:
                        code = parts[0]
                        description = ' '.join(parts[1:unit_index-2])
                        box_number = int(parts[unit_index-2])
                        pieces = float(parts[unit_index-1].replace(',', ''))
                        unit = parts[unit_index]
                        price = float(parts[unit_index+1].replace('$', ''))
                        total = float(parts[unit_index+2].replace('$', ''))
                        
                        items.append({
                            'Código': code,
                            'Descripción': description,
                            'No. Caja': box_number,
                            'Piezas': pieces,
                            'Unidad': unit,
                            'Precio': price,
                            'Importe': total
                        })
                except Exception as e:
                    print(f"Error processing line: {line}")
                    print(f"Error: {str(e)}")
                    continue
        
        return items
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return None

# Routes
@app.route('/upload_remision', methods=['GET', 'POST'])
def upload_remision():
    if request.method == 'POST':
        if 'remision' not in request.files:
            return 'No file uploaded', 400
            
        file = request.files['remision']
        if file.filename == '':
            return 'No file selected', 400
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the image
            items = process_remision_image(filepath)
            if items:
                # Create Excel file in memory
                output = io.BytesIO()
                df = pd.DataFrame(items)
                
                # Calculate total
                total = sum(item['Importe'] for item in items)
                
                # Create Excel writer
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Remisión')
                
                output.seek(0)
                
                # Clean up the uploaded file
                os.remove(filepath)
                
                return send_file(
                    output,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=f'remision_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
                )
            else:
                return 'Error processing image', 500
                
        return 'Invalid file type', 400
        
    return render_template('upload_remision.html')


@app.route('/api/products', methods=['GET'])
def get_products():
    db = get_db()
    products = list(db.products.find())
    for product in products:
        product['_id'] = str(product['_id'])
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.json
    db = get_db()
    product = Product.create_product(
        db,
        name=data['name'],
        price=data['price'],
        stock=data.get('stock', 0),
        description=data.get('description'),
        sku=data.get('sku'),
        image_url=data.get('image_url'),
        min_stock=data.get('min_stock', 0)
    )
    product['_id'] = str(product['_id'])
    return jsonify(product), 201

@app.route('/api/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.json
    db = get_db()
    Product.update_product(db, product_id, **data)
    updated_product = Product.get_by_id(db, product_id)
    updated_product['_id'] = str(updated_product['_id'])
    return jsonify(updated_product)

@app.route('/api/sales', methods=['POST'])
def create_sale():
    data = request.json
    db = get_db()
    cliente_default = db.clients.find_one({"name": "Cliente General"})
    if not cliente_default:
            cliente_default = Client.create_client(
                db,
                name="Cliente General",
                email="general@example.com",
                phone="0000000000"
            )

    # Todas las ventas son en efectivo
    metodo_pago = 'efectivo'
    
    # Crear la venta
    venta = {
                    'timestamp': datetime.now(),
                    'total': str(data['total_amount']),
                    'payment_method': metodo_pago,
                    'client_id': str(cliente_default['_id']),
                    'products': [str(data['details'][0]['product_id'])]
                }
    
    # Guardar en MongoDB
    db.sales.insert_one(venta)
    
    # Update product stock
    for detail in data['details']:
        product = Product.get_by_id(db, detail['product_id'])
        if product:
            new_stock = product['stock'] - detail['quantity']
            Product.update_product(db, detail['product_id'], stock=new_stock)
    
    sale = db.sales.find_one({"_id": venta['_id']})
    sale['_id'] = str(sale['_id'])
    return jsonify(sale), 201

@app.route('/api/sales/<sale_id>', methods=['GET'])
def get_sale(sale_id):
    db = get_db()
    sale = Sale.get_by_id(db, sale_id)
    if sale:
        sale['_id'] = str(sale['_id'])
        return jsonify(sale)
    return jsonify({"error": "Sale not found"}), 404

@app.route('/api/clients', methods=['POST'])
def create_client():
    data = request.json
    db = get_db()
    client = Client.create_client(
        db,
        name=data['name'],
        email=data.get('email'),
        phone=data.get('phone'),
        rfc=data.get('rfc'),
        address=data.get('address')
    )
    client['_id'] = str(client['_id'])
    return jsonify(client), 201

@app.route('/api/clients/<client_id>', methods=['GET'])
def get_client(client_id):
    db = get_db()
    client = Client.get_by_id(db, client_id)
    if client:
        client['_id'] = str(client['_id'])
        return jsonify(client)
    return jsonify({"error": "Client not found"}), 404


if __name__ == '__main__':
    app.run(debug=True)
