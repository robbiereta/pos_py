from convertir_ventas import create_app
from datetime import datetime

def verificar_ventas():
    app = create_app()
    
    with app.app_context():
        try:
            db = app.db
            
            # Obtener las últimas 5 ventas
            ventas = list(db.sales.find().sort('timestamp', -1).limit(5))
            
            print("\nÚltimas 5 ventas:")
            for venta in ventas:
                print(f"\nVenta ID: {venta.get('_id')}")
                print(f"  Fecha: {venta.get('timestamp')}")
                print(f"  Monto: ${float(venta.get('amount', 0)):,.2f}")
                print(f"  Método de pago: {venta.get('payment_method', 'N/A')}")
            
            # Obtener estadísticas generales
            total_ventas = db.sales.count_documents({})
            pipeline = [
                {
                    '$group': {
                        '_id': None,
                        'total': {'$sum': {'$toDouble': '$amount'}}
                    }
                }
            ]
            resultado = list(db.sales.aggregate(pipeline))
            suma_total = resultado[0]['total'] if resultado else 0
            
            print("\nEstadísticas Generales:")
            print(f"Total de ventas en la base de datos: {total_ventas}")
            print(f"Monto total en la base de datos: ${suma_total:,.2f}")
            
            # Mostrar ventas por mes
            pipeline_mensual = [
                {
                    '$group': {
                        '_id': {
                            'year': {'$year': '$timestamp'},
                            'month': {'$month': '$timestamp'}
                        },
                        'total': {'$sum': {'$toDouble': '$amount'}},
                        'count': {'$sum': 1}
                    }
                },
                {'$sort': {'_id': 1}}
            ]
            ventas_por_mes = list(db.sales.aggregate(pipeline_mensual))
            
            print("\nVentas por mes:")
            for mes in ventas_por_mes:
                year = mes['_id']['year']
                month = mes['_id']['month']
                print(f"{year}-{month:02d}: {mes['count']} ventas, ${mes['total']:,.2f}")
            
        except Exception as e:
            print(f"Error al verificar ventas: {str(e)}")

if __name__ == "__main__":
    verificar_ventas()
