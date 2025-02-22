from convertir_ventas import create_app

def reset_invoice_status():
    try:
        app = create_app()
        with app.app_context():
            # Reset is_invoiced flag for all sales
            result = app.db.sales.update_many(
                {},  # Match all documents
                {
                    "$set": {"is_invoiced": False},
                    "$unset": {"global_invoice_id": ""}  # Remove reference to global invoice
                }
            )
            
            # Delete all global invoices
            app.db.global_invoices.delete_many({})
            
            print(f"\nReset {result.modified_count} sales to non-invoiced status")
            print("Deleted all global invoices")
            
            # Verify the reset
            total_sales = app.db.sales.count_documents({})
            pending_sales = app.db.sales.count_documents({"is_invoiced": False})
            print(f"\nVerification:")
            print(f"Total Sales: {total_sales}")
            print(f"Pending Sales: {pending_sales}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    reset_invoice_status()
