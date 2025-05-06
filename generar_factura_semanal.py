from convertir_ventas import create_app
from datetime import datetime, timedelta
from cfdi_generator import CFDIGenerator

def generar_factura_semanal(fecha_inicio_str):
    """
    Genera una factura global para una semana específica
    fecha_inicio_str: fecha de inicio en formato 'YYYY-MM-DD'
    """
    app = create_app()
    
    with app.app_context():
        try:
            db = app.db
            
            # Convertir la fecha de inicio a datetime
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
            # La fecha final es 6 días después (para completar una semana), o hasta el final del mes para la última semana
            if fecha_inicio_str == '2025-04-16':
                fecha_fin = datetime(2025, 4, 30, 23, 59, 59)
            else:
                fecha_fin = fecha_inicio + timedelta(days=6, hours=23, minutes=59, seconds=59)
            
            print(f"\nGenerando factura para la semana del {fecha_inicio.strftime('%Y-%m-%d')} al {fecha_fin.strftime('%Y-%m-%d')}")
            
            # Obtener las ventas de la semana, solo las no facturadas
            ventas = list(db.sales.find({
                "timestamp": {
                    "$gte": fecha_inicio,
                    "$lte": fecha_fin
                },
                "is_invoiced": {"$ne": True}
            }))
            
            if not ventas:
                print("No hay ventas nuevas en este período.")
                return
            
            # Convertir las ventas al formato esperado y calcular totales
            ventas_procesadas = []
            total_efectivo = 0
            total_tarjeta = 0
            total_transferencia = 0
            
            for venta in ventas:
                monto = float(venta['amount'])
                metodo_pago = venta['payment_method']
                
                # Sumar al total correspondiente
                if metodo_pago == 'efectivo':
                    total_efectivo += monto
                elif metodo_pago == 'tarjeta':
                    total_tarjeta += monto
                elif metodo_pago == 'transferencia':
                    total_transferencia += monto
                
                venta_dict = {
                    '_id': venta['_id'],
                    'timestamp': venta['timestamp'],
                    'total_amount': monto,
                    'payment_method': metodo_pago
                }
                ventas_procesadas.append(venta_dict)
            
            total_amount = total_efectivo + total_tarjeta + total_transferencia
            
            # El IVA ya está incluido en el total, así que lo extraemos (16%)
            subtotal = total_amount / 1.16
            tax_amount = total_amount - subtotal
            
            print("\nResumen de ventas:")
            print(f"Total en efectivo: ${total_efectivo:,.2f}")
            print(f"Total en tarjeta: ${total_tarjeta:,.2f}")
            print(f"Total en transferencia: ${total_transferencia:,.2f}")
            print(f"Total general: ${total_amount:,.2f}")
            print(f"Subtotal: ${subtotal:,.2f}")
            print(f"IVA: ${tax_amount:,.2f}")
            
            # Obtener fecha y hora actual
            current_datetime = datetime.now()
            
            print(f"\nGenerando CFDI Global para {len(ventas_procesadas)} ventas...")
            
            # Inicializar generador de CFDI
            cfdi_generator = CFDIGenerator(test_mode=False)
            
            # Generar CFDI
            result = cfdi_generator.generate_global_cfdi(ventas_procesadas, current_datetime, db)
            
            # Imprimir resultado
            print("\n¡CFDI Generado Exitosamente!")
            print(f"UUID: {result['uuid']}")
            print(f"Folio: {result['folio']}")
            
            # Crear registro de factura global
            global_invoice = {
                'date': current_datetime,
                'start_date': fecha_inicio,
                'end_date': fecha_fin,
                'total_amount': total_amount,
                'tax_amount': tax_amount,
                'cfdi_uuid': result['uuid'],
                'folio': result['folio'],
                'xml_content': result['xml'],
                'sale_ids': [str(venta['_id']) for venta in ventas],
                'total_efectivo': total_efectivo,
                'total_tarjeta': total_tarjeta,
                'total_transferencia': total_transferencia
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
            print(f"Ventas incluidas: {len(ventas)}")
            
            return result
            
        except Exception as e:
            print(f"Error al generar la factura global: {str(e)}")
            return None

if __name__ == "__main__":
    # Generar factura para la segunda quincena de abril 2025
    generar_factura_semanal('2025-04-16')
