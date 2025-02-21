from flask import Blueprint, send_file
import pandas as pd
from io import BytesIO
from datetime import datetime
from models import Sale, Product, Client
from db import db

export_bp = Blueprint('export', __name__)

@export_bp.route('/export/sales', methods=['GET'])
def export_sales():
    """Export sales data to Excel"""
    # Query all sales
    sales = Sale.query.all()
    
    # Create a list to store sale data
    sales_data = []
    
    for sale in sales:
        # Get client info
        client = Client.query.get(sale.client_id) if sale.client_id else None
        client_name = client.name if client else "Público General"
        client_rfc = client.rfc if client else "XAXX010101000"
        
        # Get items from sale
        for item in sale.items:
            product = Product.query.get(item.product_id)
            sales_data.append({
                'Fecha': sale.date,
                'Folio': sale.folio,
                'Cliente': client_name,
                'RFC': client_rfc,
                'Producto': product.name,
                'Cantidad': item.quantity,
                'Precio Unitario': item.unit_price,
                'Subtotal': item.subtotal,
                'IVA': item.tax,
                'Total': item.total,
                'Método de Pago': sale.payment_method,
                'Estado Facturación': 'Facturado' if sale.invoiced else 'Pendiente'
            })
    
    # Create DataFrame
    df = pd.DataFrame(sales_data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Ventas')
        
        # Auto-adjust columns width
        worksheet = writer.sheets['Ventas']
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_length
    
    output.seek(0)
    
    # Generate filename with current date
    filename = f'ventas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@export_bp.route('/export/products', methods=['GET'])
def export_products():
    """Export products data to Excel"""
    # Query all products
    products = Product.query.all()
    
    # Create list of product data
    products_data = [{
        'Código': product.code,
        'Nombre': product.name,
        'Descripción': product.description,
        'Precio': product.price,
        'Unidad': product.unit,
        'Clave SAT': product.sat_key,
        'Unidad SAT': product.sat_unit,
        'IVA': product.tax_included,
        'Activo': product.active
    } for product in products]
    
    # Create DataFrame
    df = pd.DataFrame(products_data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Productos')
        
        # Auto-adjust columns width
        worksheet = writer.sheets['Productos']
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_length
    
    output.seek(0)
    
    # Generate filename with current date
    filename = f'productos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )
