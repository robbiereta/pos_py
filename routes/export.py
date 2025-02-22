from flask import Blueprint, send_file
import pandas as pd
from io import BytesIO
from datetime import datetime
from models import Sale, Product, Client
from db import get_db

export_bp = Blueprint('export', __name__)

@export_bp.route('/export/sales', methods=['GET'])
def export_sales():
    """Export sales data to Excel"""
    # Get database connection
    db = get_db()
    
    # Query all sales
    sales = db.sales.find()
    
    # Create a list to store sale data
    sales_data = []
    
    for sale in sales:
        # Get client info
        client = db.clients.find_one({'_id': sale.get('client_id')}) if sale.get('client_id') else None
        
        # Get sale details
        details = db.sale_details.find({'sale_id': sale['_id']})
        
        for detail in details:
            # Get product info
            product = db.products.find_one({'_id': detail.get('product_id')})
            
            if product:
                sales_data.append({
                    'Sale ID': str(sale['_id']),
                    'Date': sale.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S'),
                    'Client': client.get('name', 'N/A') if client else 'N/A',
                    'Product': product.get('name', 'N/A'),
                    'Quantity': detail.get('quantity', 0),
                    'Price': detail.get('price', 0),
                    'Total': detail.get('quantity', 0) * detail.get('price', 0),
                    'Amount Received': sale.get('amount_received', 0),
                    'Change': sale.get('change_amount', 0)
                })
    
    # Create DataFrame
    df = pd.DataFrame(sales_data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sales', index=False)
    
    output.seek(0)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'sales_report_{timestamp}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@export_bp.route('/export/products', methods=['GET'])
def export_products():
    """Export products data to Excel"""
    # Get database connection
    db = get_db()
    
    # Query all products
    products = db.products.find()
    
    # Create a list to store product data
    products_data = []
    
    for product in products:
        products_data.append({
            'ID': str(product['_id']),
            'Name': product.get('name', 'N/A'),
            'SKU': product.get('sku', 'N/A'),
            'Description': product.get('description', 'N/A'),
            'Price': product.get('price', 0),
            'Stock': product.get('stock', 0),
            'Min Stock': product.get('min_stock', 0),
            'Created At': product.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S'),
            'Updated At': product.get('updated_at', '').strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # Create DataFrame
    df = pd.DataFrame(products_data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Products', index=False)
    
    output.seek(0)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'products_report_{timestamp}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )
