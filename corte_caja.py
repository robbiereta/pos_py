from app import create_app
from models import db, Sale
from datetime import datetime, timedelta
from collections import defaultdict
import json
import locale

def generar_corte_caja():
    app = create_app()
    
    # Configurar locale para formato de moneda
    locale.setlocale(locale.LC_ALL, 'es_MX.UTF-8')
    
    with app.app_context():
        try:
            # Obtener todas las ventas
            ventas = Sale.query.order_by(Sale.timestamp).all()
            
            # Agrupar ventas por día
            ventas_por_dia = defaultdict(list)
            for venta in ventas:
                fecha = venta.timestamp.date()
                ventas_por_dia[fecha].append(venta)
            
            # Imprimir corte de caja por día
            print("\n=== CORTE DE CAJA DIARIO ===")
            print("Fecha de generación:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print("-" * 50)
            
            total_general = 0
            
            for fecha in sorted(ventas_por_dia.keys()):
                ventas_dia = ventas_por_dia[fecha]
                total_dia = sum(v.total_amount for v in ventas_dia)
                total_general += total_dia
                
                # Estadísticas del día
                min_venta = min(v.total_amount for v in ventas_dia)
                max_venta = max(v.total_amount for v in ventas_dia)
                promedio = total_dia / len(ventas_dia)
                
                # Productos vendidos
                productos_vendidos = defaultdict(lambda: {'cantidad': 0, 'total': 0})
                for venta in ventas_dia:
                    productos = json.loads(venta.products)
                    for producto in productos:
                        productos_vendidos[producto['id']]['cantidad'] += producto['quantity']
                        productos_vendidos[producto['id']]['total'] += producto['price']
                
                print(f"\nFecha: {fecha.strftime('%d/%m/%Y')}")
                print(f"Total de ventas: {len(ventas_dia)}")
                print(f"Monto total: ${total_dia:,.2f}")
                print(f"Venta mínima: ${min_venta:,.2f}")
                print(f"Venta máxima: ${max_venta:,.2f}")
                print(f"Promedio por venta: ${promedio:,.2f}")
                
                print("\nProductos vendidos:")
                for prod_id, datos in productos_vendidos.items():
                    print(f"- Producto #{prod_id}:")
                    print(f"  Cantidad: {datos['cantidad']}")
                    print(f"  Total: ${datos['total']:,.2f}")
                    print(f"  Promedio: ${datos['total']/datos['cantidad']:,.2f}")
                
                print("-" * 50)
            
            # Resumen general
            print("\n=== RESUMEN GENERAL ===")
            print(f"Período: {min(ventas_por_dia.keys()).strftime('%d/%m/%Y')} - {max(ventas_por_dia.keys()).strftime('%d/%m/%Y')}")
            print(f"Total de días: {len(ventas_por_dia)}")
            print(f"Total de ventas: {sum(len(v) for v in ventas_por_dia.values())}")
            print(f"Monto total: ${total_general:,.2f}")
            print(f"Promedio diario: ${total_general/len(ventas_por_dia):,.2f}")
            
        except Exception as e:
            print(f"Error generando el corte de caja: {str(e)}")

if __name__ == "__main__":
    generar_corte_caja()
