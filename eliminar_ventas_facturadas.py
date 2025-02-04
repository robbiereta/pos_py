from app import create_app
from models import db, Sale, GlobalInvoice, Invoice

def eliminar_ventas_facturadas():
    app = create_app()
    
    with app.app_context():
        try:
            # Obtener todas las ventas facturadas
            ventas_facturadas = Sale.query.filter_by(is_invoiced=True).all()
            total_ventas = len(ventas_facturadas)
            
            if total_ventas == 0:
                print("No hay ventas facturadas para eliminar.")
                return
            
            print(f"\nSe encontraron {total_ventas} ventas facturadas:")
            for venta in ventas_facturadas:
                print(f"- Venta #{venta.id}: ${venta.total_amount:,.2f} ({venta.timestamp})")
            
            # Obtener todas las facturas globales
            facturas_globales = GlobalInvoice.query.all()
            total_facturas_globales = len(facturas_globales)
            
            # Obtener todas las facturas individuales
            facturas_individuales = Invoice.query.all()
            total_facturas_individuales = len(facturas_individuales)
            
            if total_facturas_globales > 0:
                print(f"\nSe encontraron {total_facturas_globales} facturas globales:")
                for factura in facturas_globales:
                    print(f"- Factura {factura.cfdi_uuid}: ${factura.total_amount:,.2f} ({factura.date})")
            
            if total_facturas_individuales > 0:
                print(f"\nSe encontraron {total_facturas_individuales} facturas individuales")
            
            # Confirmar eliminación
            confirmacion = input("\n¿Estás seguro de que deseas eliminar todas las ventas facturadas? (s/n): ")
            if confirmacion.lower() != 's':
                print("Operación cancelada.")
                return
            
            # Eliminar facturas individuales primero
            if total_facturas_individuales > 0:
                print("\nEliminando facturas individuales...")
                for factura in facturas_individuales:
                    db.session.delete(factura)
                print(f"- {total_facturas_individuales} facturas individuales eliminadas")
            
            # Eliminar facturas globales
            if total_facturas_globales > 0:
                print("\nEliminando facturas globales...")
                for factura in facturas_globales:
                    db.session.delete(factura)
                print(f"- {total_facturas_globales} facturas globales eliminadas")
            
            # Eliminar ventas facturadas
            print("\nEliminando ventas facturadas...")
            for venta in ventas_facturadas:
                db.session.delete(venta)
            
            # Guardar cambios
            db.session.commit()
            
            print(f"\n¡Operación completada!")
            print(f"- {total_ventas} ventas facturadas eliminadas")
            if total_facturas_individuales > 0:
                print(f"- {total_facturas_individuales} facturas individuales eliminadas")
            if total_facturas_globales > 0:
                print(f"- {total_facturas_globales} facturas globales eliminadas")
            
        except Exception as e:
            db.session.rollback()
            print(f"\nError durante la eliminación: {str(e)}")
            print("Se ha revertido la operación.")

if __name__ == "__main__":
    eliminar_ventas_facturadas()
