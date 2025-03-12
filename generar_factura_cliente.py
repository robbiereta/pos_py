from models import GlobalInvoice
from convertir_ventas import create_app
from datetime import datetime, date
from cfdi_generator import CFDIGenerator 
import os

def generar_factura_cliente():
    app = create_app()
    
    with app.app_context():
        try:
            # Obtener ventas no facturadas
            sales = list(app.db.sales.find({"is_invoiced": False}))
            
            if not sales:
                print("No hay ventas pendientes por facturar.")
                return
            
            print(f"\nGenerando factura de cliente  para la  nota {sales[0]['_id']}")
            
            # Calcular totales
            total_amount = sum(sale['total_amount'] for sale in sales)
            # El IVA ya está incluido en el total, así que lo extraemos (16%)
            subtotal = total_amount / 1.16
            tax_amount = total_amount - subtotal
            
            # Get current date and time
            current_datetime = datetime.now()

            print(f"\nGenerating Global CFDI for {len(sales)} sales on {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

            # Initialize CFDI Generator
            cfdi_generator = CFDIGenerator(test_mode=False)

            # Generate CFDI
            result = cfdi_generator.generate_global_cfdi(sales, current_datetime)
            
            # Print result
            print("\nCFDI Generated Successfully!")
            print(f"UUID: {result['uuid']}")
            print(f"Folio: {result['folio']}")
            
            # Crear registro de factura global
            global_invoice = GlobalInvoice.create_global_invoice(
                db=app.db,
                date=current_datetime.isoformat(),  # Convert date to string
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
            
            # Mark sales as invoiced
            for sale in sales:
                app.db.sales.update_one(
                    {'_id': sale['_id']},
                    {'$set': {
                        'is_invoiced': True,
                        'invoice_uuid': result['uuid'],
                        'invoice_date': current_datetime
                    }}
                )
            
            print(f"\nMarked {len(sales)} sales as invoiced")
            
            return global_invoice
            
        except Exception as e:
            print(f"Error al generar factura global: {str(e)}")
            return None

if __name__ == "__main__":
    generar_factura_global()
