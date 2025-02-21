from flask import Blueprint, send_file
import pandas as pd
import os
from datetime import datetime
from src.core.models import Sale, Product

export_bp = Blueprint('export', __name__)

@export_bp.route('/export/sales')
def export_sales():
    try:
        # Query all sales
        sales = Sale.query.all()
        
        # Convert to DataFrame
        sales_data = []
        for sale in sales:
            for detail in sale.details:
                sales_data.append({
                    'Fecha': sale.date,
                    'Folio': sale.id,
                    'Cliente': sale.client.name if sale.client else 'Venta al público en general',
                    'Producto': detail.product.name,
                    'Cantidad': detail.quantity,
                    'Precio Unitario': detail.price,
                    'Total': detail.quantity * detail.price,
                    'Facturado': 'Sí' if sale.is_invoiced else 'No'
                })
        
        df = pd.DataFrame(sales_data)
        
        # Create Excel file
        filename = f'ventas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        filepath = os.path.join('data/output', filename)
        df.to_excel(filepath, index=False)
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return str(e), 500

@export_bp.route('/export/products')
def export_products():
    try:
        # Query all products
        products = Product.query.all()
        
        # Convert to DataFrame
        products_data = [{
            'SKU': product.sku,
            'Nombre': product.name,
            'Precio': product.price,
            'Stock': product.stock,
            'Unidad': product.unit,
            'Clave SAT': product.sat_key
        } for product in products]
        
        df = pd.DataFrame(products_data)
        
        # Create Excel file
        filename = f'productos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        filepath = os.path.join('data/output', filename)
        df.to_excel(filepath, index=False)
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return str(e), 500
