from app import create_app
from models import Sale
from datetime import datetime

def verificar_ventas():
    app = create_app()
    
    with app.app_context():
        # Obtener todas las ventas
        ventas = Sale.query.order_by(Sale.timestamp).all()
        
        # Calcular estadísticas
        total_ventas = len(ventas)
        total_monto = sum(venta.total_amount for venta in ventas)
        min_monto = min(venta.total_amount for venta in ventas) if ventas else 0
        max_monto = max(venta.total_amount for venta in ventas) if ventas else 0
        promedio = total_monto / total_ventas if total_ventas > 0 else 0
        
        # Agrupar ventas por día
        ventas_por_dia = {}
        for venta in ventas:
            fecha = venta.timestamp.strftime('%Y-%m-%d')
            if fecha not in ventas_por_dia:
                ventas_por_dia[fecha] = {'total': 0, 'count': 0}
            ventas_por_dia[fecha]['total'] += venta.total_amount
            ventas_por_dia[fecha]['count'] += 1
        
        print("\n=== RESUMEN DE VENTAS EN BASE DE DATOS ===")
        print(f"Total de ventas: {total_ventas}")
        print(f"Monto total: ${total_monto:,.2f}")
        print(f"Venta mínima: ${min_monto:,.2f}")
        print(f"Venta máxima: ${max_monto:,.2f}")
        print(f"Promedio por venta: ${promedio:,.2f}")
        
        print("\n=== VENTAS POR DÍA ===")
        for fecha in sorted(ventas_por_dia.keys()):
            info = ventas_por_dia[fecha]
            print(f"{fecha}: ${info['total']:,.2f} ({info['count']} ventas)")
        
        print("\n=== ÚLTIMAS 5 VENTAS ===")
        for venta in ventas[-5:]:
            print(f"\nVenta #{venta.id}:")
            print(f"  Fecha: {venta.timestamp}")
            print(f"  Monto: ${venta.total_amount:,.2f}")
            print(f"  Productos: {venta.products}")

if __name__ == "__main__":
    verificar_ventas()
