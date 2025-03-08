from convertir_ventas import create_app
from corte_caja_mongo import CorteCajaMongo
from datetime import datetime, timedelta

def generar_corte_diario(fecha=None):
    """
    Genera un corte de caja para un día específico
    fecha: fecha para el corte (str en formato YYYY-MM-DD o datetime)
            Si no se especifica, se usa la fecha actual
    """
    app = create_app()
    
    with app.app_context():
        try:
            db = app.db
            cortes = CorteCajaMongo(db)
            
            # Procesar la fecha
            if isinstance(fecha, str):
                fecha = datetime.strptime(fecha, '%Y-%m-%d')
            elif fecha is None:
                fecha = datetime.now()
            
            # Definir el rango del día
            inicio_dia = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
            fin_dia = fecha.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            print(f"\nGenerando corte para el día {fecha.strftime('%Y-%m-%d')}")
            
            # Obtener ventas del día
            ventas = list(db.sales.find({
                "timestamp": {
                    "$gte": inicio_dia,
                    "$lte": fin_dia
                }
            }))
            
            # Calcular totales por método de pago
            total_efectivo = sum(float(v['amount']) for v in ventas if v['payment_method'] == 'efectivo')
            total_tarjeta = sum(float(v['amount']) for v in ventas if v['payment_method'] == 'tarjeta')
            total_transferencia = sum(float(v['amount']) for v in ventas if v['payment_method'] == 'transferencia')
            
            # Obtener el monto inicial del día
            corte_anterior = cortes.obtener_ultimo_corte()
            monto_inicial = float(corte_anterior['monto_final']) if corte_anterior else 1000.00
            
            # Calcular monto final
            monto_final = monto_inicial + total_efectivo - float(corte_anterior.get('retiros', 0)) if corte_anterior else monto_inicial + total_efectivo
            
            print("\nResumen del corte:")
            print(f"Fecha: {fecha.strftime('%Y-%m-%d')}")
            print(f"Monto inicial: ${monto_inicial:,.2f}")
            print(f"Ventas en efectivo: ${total_efectivo:,.2f}")
            print(f"Ventas con tarjeta: ${total_tarjeta:,.2f}")
            print(f"Ventas por transferencia: ${total_transferencia:,.2f}")
            print(f"Total de ventas: ${(total_efectivo + total_tarjeta + total_transferencia):,.2f}")
            print(f"Monto final: ${monto_final:,.2f}")
            print(f"Número de ventas: {len(ventas)}")
            
            # Crear el corte
            corte_id = cortes.crear_corte(
                monto_inicial=monto_inicial,
                monto_final=monto_final,
                ventas_efectivo=total_efectivo,
                ventas_tarjeta=total_tarjeta,
                ventas_transferencia=total_transferencia,
                notas=f"Corte automático del {fecha.strftime('%Y-%m-%d')}"
            )
            
            print(f"\n¡Corte generado exitosamente!")
            print(f"ID del corte: {corte_id}")
            
            return corte_id
            
        except Exception as e:
            print(f"Error al generar el corte: {str(e)}")
            return None

def generar_cortes_faltantes(inicio, fin):
    """
    Genera cortes para un rango de fechas
    inicio: fecha inicial (str en formato YYYY-MM-DD)
    fin: fecha final (str en formato YYYY-MM-DD)
    """
    fecha_inicio = datetime.strptime(inicio, '%Y-%m-%d')
    fecha_fin = datetime.strptime(fin, '%Y-%m-%d')
    
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        generar_corte_diario(fecha_actual)
        fecha_actual += timedelta(days=1)

if __name__ == "__main__":
    # Generar cortes para todo marzo 2025
    generar_cortes_faltantes('2025-03-01', '2025-03-31')
