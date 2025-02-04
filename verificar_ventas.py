from app import create_app
from models import Sale

def verificar_ventas():
    app = create_app()
    
    with app.app_context():
        # Obtener las últimas 5 ventas
        ventas = Sale.query.order_by(Sale.timestamp.desc()).limit(5).all()
        
        print("\nÚltimas 5 ventas importadas:")
        for venta in ventas:
            print(f"\nVenta #{venta.id}:")
            print(f"  Fecha: {venta.timestamp}")
            print(f"  Monto: ${venta.total_amount:,.2f}")
            print(f"  Productos: {venta.products}")
        
        # Obtener estadísticas generales
        total_ventas = Sale.query.count()
        suma_total = sum(venta.total_amount for venta in Sale.query.all())
        
        print("\nEstadísticas Generales:")
        print(f"Total de ventas en la base de datos: {total_ventas}")
        print(f"Monto total en la base de datos: ${suma_total:,.2f}")

if __name__ == "__main__":
    verificar_ventas()
