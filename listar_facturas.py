from models import db, Invoice, GlobalInvoice
from datetime import datetime, timedelta
from app import create_app
import os

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pos.db'

# Obtener facturas del último año
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

print(f"\nBuscando facturas desde {start_date.date()} hasta {end_date.date()}\n")

with app.app_context():
    # Obtener facturas individuales
    invoices = Invoice.query.filter(
        Invoice.timestamp >= start_date,
        Invoice.timestamp <= end_date
    ).order_by(Invoice.timestamp.desc()).all()
    
    print("\nFacturas Individuales:")
    print(f"Total encontradas: {len(invoices)}\n")
    
    for invoice in invoices:
        print(f"UUID: {invoice.cfdi_uuid}")
        print(f"Fecha: {invoice.timestamp}")
        print(f"Venta ID: {invoice.sale_id}")
        print("-" * 50)
    
    # Obtener facturas globales
    global_invoices = GlobalInvoice.query.filter(
        GlobalInvoice.date >= start_date.date(),
        GlobalInvoice.date <= end_date.date()
    ).order_by(GlobalInvoice.date.desc()).all()
    
    print("\n\nFacturas Globales:")
    print(f"Total encontradas: {len(global_invoices)}")
    
    # Debug: mostrar todas las facturas globales
    print("\nDetalles de facturas globales:")
    for invoice in global_invoices:
        print(f"UUID: {invoice.cfdi_uuid}")
        print(f"Fecha: {invoice.date}")
        print(f"Total: ${invoice.total_amount:.2f}")
        print(f"IVA: ${invoice.tax_amount:.2f}")
        print(f"Ventas incluidas: {len(invoice.sales)}")
        print("-" * 50)
