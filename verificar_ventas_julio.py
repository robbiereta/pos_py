from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Conectar a la base de datos
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['pos_db']

# Definir rango de fechas para julio 2025
start_date = datetime(2025, 7, 1)
end_date = datetime(2025, 8, 1)

# Obtener todas las ventas para analizar las fechas
all_sales = list(db.sales.find().sort('sale_date', 1))

# Filtrar manualmente las ventas de julio 2025 para diagnóstico
sales = []
for sale in all_sales:
    sale_date = sale.get('sale_date')
    if sale_date and isinstance(sale_date, datetime):
        if sale_date.month == 7 and sale_date.year == 2025:
            sales.append(sale)
        else:
            print(f"Venta fuera de julio 2025: {sale_date}")
    else:
        print(f"Venta con fecha inválida: {sale.get('_id')} - {sale_date}")

print(f"\nTotal de ventas en la base de datos: {len(all_sales)}")
print(f"Ventas filtradas manualmente para julio 2025: {len(sales)}")

# Mostrar resumen
print(f'\nTotal de ventas en julio 2025: {len(sales)}')

if sales:
    print('\nPrimeras 5 ventas:')
    for sale in sales[:5]:
        print(f"ID: {sale['_id']}")
        print(f"  Fecha: {sale['sale_date']}")
        print(f"  Monto: {sale.get('total', 'N/A')}")
        print(f"  Método de pago: {sale.get('payment_method', 'N/A')}")
        print(f"  Estado: {sale.get('status', 'N/A')}")
        print(f"  Facturada: {sale.get('is_invoiced', False)}")
        print(f"  ID de factura: {sale.get('invoice_uuid', 'N/A')}")
        print()
    
    # Mostrar resumen de facturación
    facturadas = sum(1 for s in sales if s.get('is_invoiced', False))
    print(f'\nResumen de facturación:')
    print(f'- Total ventas: {len(sales)}')
    print(f'- Ya facturadas: {facturadas}')
    print(f'- Por facturar: {len(sales) - facturadas}')
    
    # Mostrar fechas extremas
    if len(sales) > 1:
        print(f'\nRango de fechas:')
        print(f'- Primera venta: {sales[0]["sale_date"]}')
        print(f'- Última venta: {sales[-1]["sale_date"]}')
else:
    print('No se encontraron ventas para julio 2025.')

# Verificar si hay ventas fuera de julio 2025
print('\nVerificando ventas fuera de julio 2025...')
other_sales = list(db.sales.find({
    '$or': [
        {'timestamp': {'$lt': start_date}},
        {'timestamp': {'$gte': end_date}}
    ]
}).limit(5))  # Solo las primeras 5 para muestra

if other_sales:
    print('\nAlgunas ventas fuera de julio 2025:')
    for sale in other_sales:
        print(f"- ID: {sale['_id']}, Fecha: {sale['timestamp']}, Monto: {sale.get('amount', 'N/A')}")
else:
    print('No se encontraron ventas fuera de julio 2025.')
