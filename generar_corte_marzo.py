from datetime import datetime
from convertir_ventas import create_app
from cortes_caja import CorteCaja
from pymongo import MongoClient
import os
from dotenv import load_dotenv

def calcular_ventas_marzo():
    # Cargar variables de entorno
    load_dotenv()
    
    # Crear la aplicación y obtener conexión a MongoDB
    app = create_app()
    
    # Inicializar totales
    total_efectivo = 0.0
    total_tarjeta = 0.0
    total_transferencia = 0.0
    
    with app.app_context():
        try:
            db = app.db
            
            # Definir el rango de fechas para marzo
            inicio_marzo = datetime(2025, 3, 1)
            fin_marzo = datetime(2025, 3, 31, 23, 59, 59)
            
            # Consultar ventas de marzo
            ventas = db.sales.find({
                'timestamp': {
                    '$gte': inicio_marzo,
                    '$lte': fin_marzo
                }
            })
            
            # Calcular totales por método de pago
            for venta in ventas:
                monto = float(venta.get('amount', 0))
                metodo_pago = venta.get('payment_method', '').lower()
                
                if metodo_pago == 'efectivo':
                    total_efectivo += monto
                elif metodo_pago == 'tarjeta':
                    total_tarjeta += monto
                elif metodo_pago == 'transferencia':
                    total_transferencia += monto
            
            # Crear el corte de caja
            cortes = CorteCaja()
            
            # Asumimos un efectivo inicial de 0 para el mes
            efectivo_inicial = 0
            # El efectivo final será el total de ventas en efectivo menos retiros (asumimos 0 retiros)
            retiros = 0
            efectivo_final = total_efectivo - retiros
            
            id_corte = cortes.crear_corte(
                efectivo_inicial=efectivo_inicial,
                efectivo_final=efectivo_final,
                ventas_efectivo=total_efectivo,
                ventas_tarjeta=total_tarjeta,
                ventas_transferencia=total_transferencia,
                retiros=retiros,
                notas=f"Corte del mes de marzo 2025"
            )
            
            print("\nCorte de caja generado exitosamente:")
            print(f"ID del corte: {id_corte}")
            print(f"Ventas en efectivo: ${total_efectivo:,.2f}")
            print(f"Ventas con tarjeta: ${total_tarjeta:,.2f}")
            print(f"Ventas por transferencia: ${total_transferencia:,.2f}")
            print(f"Total ventas: ${(total_efectivo + total_tarjeta + total_transferencia):,.2f}")
            
            return id_corte
            
        except Exception as e:
            print(f"Error al generar el corte: {str(e)}")
            return None

if __name__ == "__main__":
    calcular_ventas_marzo()
