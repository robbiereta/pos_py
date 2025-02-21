from models import db, Sale
from app import create_app
import os

def marcar_ventas_no_facturadas():
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pos.db'
    
    with app.app_context():
        try:
            # Marcar todas las ventas como no facturadas
            sales = Sale.query.all()
            count = 0
            
            if not sales:
                print("No hay ventas en el sistema.")
                return
            
            for sale in sales:
                sale.is_invoiced = False
                sale.global_invoice = None
                count += 1
            
            db.session.commit()
            print(f"Se marcaron {count} ventas como no facturadas")
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    marcar_ventas_no_facturadas()
