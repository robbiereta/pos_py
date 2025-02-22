from models import GlobalInvoice
from convertir_ventas import create_app
from datetime import datetime, date
from cfdi_generator import cfdi_generator 
import os

def generar_factura_global():
    app = create_app()
    
    with app.app_context():
        try:
            # Obtener ventas no facturadas
            sales = list(app.db.sales.find({"is_invoiced": False}))
            
            if not sales:
                print("No hay ventas pendientes por facturar.")
                return
            
            print(f"\nGenerando factura global para {len(sales)} ventas...")
            
            # Calcular totales
            total_amount = sum(sale['total_amount'] for sale in sales)
            # El IVA ya está incluido en el total, así que lo extraemos (16%)
            subtotal = total_amount / 1.16
            tax_amount = total_amount - subtotal
            
            # Generar factura global
            today = date.today()
            result = cfdi_generator.generate_global_cfdi(sales, today)
            
            # Crear registro de factura global
            global_invoice = GlobalInvoice.create_global_invoice(
                db=app.db,
                date=today.isoformat(),  # Convert date to string
                total_amount=total_amount,
                tax_amount=tax_amount,
                cfdi_uuid=result['uuid'],
                folio=result['folio'],
                xml_content=result['xml'],
                sale_ids=[sale['_id'] for sale in sales]
            )
            
            print("\nFactura global generada exitosamente:")
            print(f"UUID: {global_invoice['cfdi_uuid']}")
            print(f"Folio: {global_invoice['folio']}")
            print(f"Total: ${global_invoice['total_amount']:,.2f}")
            print(f"IVA: ${global_invoice['tax_amount']:,.2f}")
            print(f"Ventas incluidas: {len(global_invoice['sale_ids'])}")
            
            return global_invoice
            
        except Exception as e:
            print(f"Error al generar factura global: {str(e)}")
            return None

if __name__ == "__main__":
    generar_factura_global()
