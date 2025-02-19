import pandas as pd
import json
from datetime import datetime, timedelta
from collections import defaultdict
from app import create_app
from models import db, Sale, Client, SaleDetail, Product

def convertir_e_importar_ventas(archivo_origen):
    # Crear la aplicación y el contexto
    app = create_app()
    
    with app.app_context():
        try:
            # Leer el archivo de ventas original
            df = pd.read_excel(archivo_origen)
            
            # Obtener las fechas de la primera fila
            fechas = df.iloc[0]
            
            # Estadísticas
            ventas_por_dia = defaultdict(float)
            total_ventas = 0
            min_venta = float('inf')
            max_venta = 0
            ventas_importadas = 0
            
            # Obtener o crear cliente por defecto
            cliente_default = Client.query.filter_by(name='Cliente General').first()
            if not cliente_default:
                cliente_default = Client(
                    name='Cliente General',
                    email='general@example.com',
                    phone='0000000000'
                )
                db.session.add(cliente_default)
                db.session.commit()
            
            print("\nIniciando procesamiento de ventas...")
            
            # Procesar cada columna (día)
            for col in df.columns:
                fecha_str = df.iloc[0][col]
                if isinstance(fecha_str, datetime):  # Si es una fecha válida
                    # Obtener todas las ventas de ese día (ignorando NaN)
                    montos = df.iloc[1:][col].dropna()
                    
                    # Crear una venta por cada monto
                    for monto in montos:
                        if monto > 0:  # Solo procesar montos positivos
                            # Crear objeto de venta
                            venta = Sale(
                                date=fecha_str,
                                total_amount=float(monto),
                                amount_received=float(monto),
                                change_amount=0.0,
                                client_id=cliente_default.id,
                                is_invoiced=False
                            )
                            
                            # Crear detalle de venta
                            detalle = SaleDetail(
                                quantity=1,
                                price=float(monto),
                                sale=venta
                            )
                            
                            # Agregar a la base de datos
                            db.session.add(venta)
                            db.session.add(detalle)
                            
                            # Actualizar estadísticas
                            fecha_key = fecha_str.strftime('%Y-%m-%d')
                            ventas_por_dia[fecha_key] += float(monto)
                            total_ventas += float(monto)
                            min_venta = min(min_venta, float(monto))
                            max_venta = max(max_venta, float(monto))
                            ventas_importadas += 1
                            
                            # Commit cada 100 ventas
                            if ventas_importadas % 100 == 0:
                                db.session.commit()
                                print(f"Procesadas {ventas_importadas} ventas...")
            
            # Commit final
            db.session.commit()
            
            # Imprimir resumen
            print("\nResumen de importación:")
            print(f"Total de ventas importadas: {ventas_importadas}")
            print(f"Monto total: ${total_ventas:,.2f}")
            print(f"Venta mínima: ${min_venta:,.2f}")
            print(f"Venta máxima: ${max_venta:,.2f}")
            print("\nVentas por día:")
            for fecha, monto in ventas_por_dia.items():
                print(f"{fecha}: ${monto:,.2f}")
            
            return {
                'status': 'success',
                'ventas_importadas': ventas_importadas,
                'total_ventas': total_ventas,
                'ventas_por_dia': dict(ventas_por_dia)
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"Error durante la importación: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

if __name__ == "__main__":
    archivo_origen = "_ventas_feb25.xlsx"
    resultado = convertir_e_importar_ventas(archivo_origen)
    print(f"\nEstado final: {resultado['status']}")
