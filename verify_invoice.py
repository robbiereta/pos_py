from convertir_ventas import create_app
from datetime import datetime

def verify_invoice():
    try:
        app = create_app()
        with app.app_context():
            # Check global invoice
            global_invoice = app.db.global_invoices.find_one({})
            if global_invoice:
                print("\nGlobal Invoice Details:")
                print(f"UUID: {global_invoice['cfdi_uuid']}")
                print(f"Folio: {global_invoice['folio']}")
                print(f"Date: {global_invoice['date']}")
                print(f"Total Amount: ${global_invoice['total_amount']:,.2f}")
                print(f"Tax Amount: ${global_invoice['tax_amount']:,.2f}")
                print(f"Number of Sales: {len(global_invoice['sale_ids'])}")
            
            # Check sales status
            total_sales = app.db.sales.count_documents({})
            invoiced_sales = app.db.sales.count_documents({"is_invoiced": True})
            pending_sales = app.db.sales.count_documents({"is_invoiced": False})
            
            print("\nSales Status:")
            print(f"Total Sales: {total_sales}")
            print(f"Invoiced Sales: {invoiced_sales}")
            print(f"Pending Sales: {pending_sales}")
            
    except Exception as e:
        print('Error:', str(e))

if __name__ == '__main__':
    verify_invoice()
