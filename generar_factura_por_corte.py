from convertir_ventas import create_app
from datetime import datetime
from cfdi_generator import CFDIGenerator
import sqlite3

def generar_factura_por_corte():
    app = create_app()
    
    with app.app_context():
        try:
            db = app.db
            
            # Obtener el corte de caja más reciente de SQLite
            conn = sqlite3.connect("pos_database.db")
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, fecha_hora, ventas_efectivo, ventas_tarjeta, 
                       ventas_transferencia, notas
                FROM cortes_caja 
                ORDER BY created_at DESC 
                LIMIT 1
            ''')
            
            corte = cursor.fetchone()
            if not corte:
                print("No se encontraron cortes de caja")
                return
                
            corte_dict = {
                'id': corte[0],
                'fecha_hora': corte[1],
                'ventas_efectivo': corte[2],
                'ventas_tarjeta': corte[3],
                'ventas_transferencia': corte[4],
                'notas': corte[5]
            }
            
            print(f"Usando corte de caja del {corte_dict['fecha_hora']}")
            
            # Obtener el rango del mes completo
            inicio_mes = datetime(2025, 3, 1)
            fin_mes = datetime(2025, 3, 31, 23, 59, 59)
            
            print(f"Buscando ventas entre {inicio_mes} y {fin_mes}")
            
            # Verificar las ventas en la base de datos
            todas_ventas = list(db.sales.find())
            print(f"\nTotal de ventas en la base de datos: {len(todas_ventas)}")
            if todas_ventas:
                print("\nPrimeras 3 ventas:")
                for venta in todas_ventas[:3]:
                    print(f"  Fecha: {venta.get('timestamp')}")
                    print(f"  Monto: ${float(venta.get('amount', 0)):,.2f}")
                    print(f"  Método: {venta.get('payment_method')}")
                    print()
            
            ventas = list(db.sales.find({
                "timestamp": {
                    "$gte": inicio_mes,
                    "$lte": fin_mes
                }
            }))
            
            if not ventas:
                print("No hay ventas en este período.")
                return
            
            # Convertir las ventas al formato esperado
            ventas_procesadas = []
            for venta in ventas:
                venta_dict = {
                    '_id': venta['_id'],
                    'timestamp': venta['timestamp'],
                    'total_amount': float(venta['amount']),
                    'payment_method': venta['payment_method']
                }
                ventas_procesadas.append(venta_dict)
            
            print(f"\nGenerando factura global para {len(ventas_procesadas)} ventas...")
            
            # Calcular totales
            total_amount = float(corte_dict['ventas_efectivo']) + float(corte_dict['ventas_tarjeta']) + float(corte_dict['ventas_transferencia'])
            # El IVA ya está incluido en el total, así que lo extraemos (16%)
            subtotal = total_amount / 1.16
            tax_amount = total_amount - subtotal
            
            # Obtener fecha y hora actual
            current_datetime = datetime.now()
            
            print(f"\nGenerando CFDI Global para {len(ventas_procesadas)} ventas del {inicio_mes.strftime('%Y-%m-%d')}")
            
            # Inicializar generador de CFDI
            cfdi_generator = CFDIGenerator(test_mode=False)
            
            # Generar CFDI
            result = cfdi_generator.generate_global_cfdi(ventas_procesadas, current_datetime)
            
            # Imprimir resultado
            print("\n¡CFDI Generado Exitosamente!")
            print(f"UUID: {result['uuid']}")
            print(f"Folio: {result['folio']}")
            
            # Crear registro de factura global
            global_invoice = {
                'date': current_datetime,
                'total_amount': total_amount,
                'tax_amount': tax_amount,
                'cfdi_uuid': result['uuid'],
                'folio': result['folio'],
                'xml_content': result['xml'],
                'sale_ids': [str(venta['_id']) for venta in ventas],
                'corte_id': corte_dict['id']
            }
            
            # Guardar la factura global
            db.global_invoices.insert_one(global_invoice)
            
            # Marcar las ventas como facturadas
            for venta in ventas:
                db.sales.update_one(
                    {'_id': venta['_id']},
                    {'$set': {'is_invoiced': True}}
                )
            
            print(f"\nFactura global guardada exitosamente")
            print(f"Monto total: ${total_amount:,.2f}")
            print(f"IVA: ${tax_amount:,.2f}")
            print(f"Ventas incluidas: {len(ventas)}")
            
            conn.close()
            return result
            
        except Exception as e:
            print(f"Error al generar la factura global: {str(e)}")
            if 'conn' in locals():
                conn.close()
            return None

if __name__ == "__main__":
    generar_factura_por_corte()
