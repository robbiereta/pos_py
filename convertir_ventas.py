import pandas as pd
import json
from datetime import datetime, timedelta
from collections import defaultdict

def convertir_ventas(archivo_origen, archivo_destino):
    try:
        # Leer el archivo de ventas original
        df = pd.read_excel(archivo_origen)
        
        # Obtener las fechas de la segunda fila
        fechas = df.iloc[1]
        
        # Lista para almacenar todas las ventas
        ventas = []
        
        # Diccionarios para estadísticas
        ventas_por_dia = defaultdict(float)
        total_ventas = 0
        min_venta = float('inf')
        max_venta = 0
        
        # Procesar cada columna (día)
        for col in range(len(df.columns)):
            fecha_str = fechas[col]
            if isinstance(fecha_str, datetime):  # Si es una fecha válida
                # Obtener todas las ventas de ese día (ignorando NaN)
                montos = df.iloc[2:, col].dropna()
                
                # Crear una venta por cada monto
                for monto in montos:
                    if monto > 0:  # Solo procesar montos positivos
                        venta = {
                            'fecha': fecha_str.strftime('%Y-%m-%d'),
                            'total_amount': float(monto),
                            'products': json.dumps([{
                                'id': 1,  # ID del producto por defecto
                                'quantity': 1,  # Cantidad por defecto
                                'price': float(monto)  # Precio igual al monto total
                            }])
                        }
                        ventas.append(venta)
                        
                        # Actualizar estadísticas
                        fecha_key = fecha_str.strftime('%Y-%m-%d')
                        ventas_por_dia[fecha_key] += float(monto)
                        total_ventas += float(monto)
                        min_venta = min(min_venta, float(monto))
                        max_venta = max(max_venta, float(monto))
        
        # Crear DataFrame con las ventas convertidas
        df_ventas = pd.DataFrame(ventas)
        
        # Guardar como Excel
        df_ventas.to_excel(archivo_destino, index=False)
        
        # Mostrar resumen detallado
        print("\n=== RESUMEN DE CONVERSIÓN ===")
        print(f"Total de ventas procesadas: {len(ventas)}")
        print(f"Monto total de ventas: ${total_ventas:,.2f}")
        print(f"Venta mínima: ${min_venta:,.2f}")
        print(f"Venta máxima: ${max_venta:,.2f}")
        print(f"Promedio por venta: ${total_ventas/len(ventas):,.2f}")
        
        print("\n=== VENTAS POR DÍA ===")
        for fecha, total in sorted(ventas_por_dia.items()):
            num_ventas = len([v for v in ventas if v['fecha'] == fecha])
            print(f"{fecha}: ${total:,.2f} ({num_ventas} ventas)")
        
        print("\n=== MUESTRA DE VENTAS CONVERTIDAS ===")
        print("Primeras 5 ventas:")
        for i, venta in enumerate(ventas[:5]):
            print(f"\nVenta #{i+1}:")
            print(f"  Fecha: {venta['fecha']}")
            print(f"  Monto: ${venta['total_amount']:,.2f}")
            print(f"  Productos: {venta['products']}")
        
        print(f"\nArchivo guardado como: {archivo_destino}")
        print("Las ventas están listas para ser importadas al sistema.")
        
    except Exception as e:
        print(f"Error durante la conversión: {str(e)}")

if __name__ == "__main__":
    archivo_origen = "ventasenero25_parte2.xlsx"
    archivo_destino = "ventas_enero_parte2_convertidas.xlsx"
    
    print("Iniciando conversión de ventas...")
    convertir_ventas(archivo_origen, archivo_destino)
