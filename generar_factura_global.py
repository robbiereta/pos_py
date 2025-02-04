from models import db, Sale, GlobalInvoice, Invoice
from cfdi_generator import cfdi_generator  # Usar el generador de prueba
from datetime import datetime, date
from app import create_app
import os

def generar_factura_global():
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pos.db'

    with app.app_context():
        try:
            # Obtener ventas no facturadas
            sales = Sale.query.filter_by(is_invoiced=False).all()
            
            if not sales:
                print("No hay ventas pendientes por facturar.")
                return
            
            print(f"\nGenerando factura global para {len(sales)} ventas...")
            
            # Calcular totales
            total_amount = sum(sale.total_amount for sale in sales)
            # El IVA ya está incluido en el total, así que lo extraemos (16%)
            subtotal = total_amount / 1.16
            tax_amount = total_amount - subtotal
            
            # Generar factura global
            result = cfdi_generator.generate_global_cfdi(sales, date.today())
            
            # Crear registro de factura global
            global_invoice = GlobalInvoice(
                date=date.today(),
                total_amount=total_amount,
                tax_amount=tax_amount,
                cfdi_uuid=result['uuid'],
                xml_content=result['xml']
            )
            
            # Guardar factura global
            db.session.add(global_invoice)
            
            # Marcar ventas como facturadas y asociarlas a la factura global
            for sale in sales:
                sale.is_invoiced = True
                sale.global_invoice = global_invoice
            
            # Guardar cambios
            db.session.commit()
            
            print("\nFactura global generada exitosamente:")
            print(f"UUID: {result['uuid']}")
            print(f"Subtotal: ${subtotal:.2f}")
            print(f"IVA: ${tax_amount:.2f}")
            print(f"Total: ${total_amount:.2f}")
            print(f"Ventas incluidas: {len(sales)}")
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    generar_factura_global()
