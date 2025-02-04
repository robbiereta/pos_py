from app import create_app
from models import db, Sale
import pandas as pd
from datetime import datetime
from convertir_ventas import convertir_ventas

def importar_ventas(archivo_excel_origen):
    # Crear la aplicación y el contexto
    app = create_app()
    
    with app.app_context():
        try:
            print("\nConvirtiendo ventas del archivo:", archivo_excel_origen)
            df_ventas = convertir_ventas(archivo_excel_origen, "temp_ventas_convertidas.xlsx")
            
            if df_ventas is None:
                print("Error durante la conversión de ventas.")
                return
            
            # Contador de ventas importadas
            ventas_importadas = 0
            total_monto = 0
            
            print("\nIniciando importación de ventas...")
            
            # Procesar cada venta
            for _, row in df_ventas.iterrows():
                try:
                    # Crear objeto de venta
                    venta = Sale(
                        timestamp=datetime.strptime(row['fecha'], '%Y-%m-%d'),
                        total_amount=float(row['total_amount']),
                        products=row['products']  # Ya está en formato JSON
                    )
                    
                    # Agregar a la base de datos
                    db.session.add(venta)
                    ventas_importadas += 1
                    total_monto += float(row['total_amount'])
                    
                    # Commit cada 100 ventas para no sobrecargar la memoria
                    if ventas_importadas % 100 == 0:
                        db.session.commit()
                        print(f"Procesadas {ventas_importadas} ventas...")
                    
                except Exception as e:
                    print(f"Error procesando venta: {str(e)}")
                    continue
            
            # Commit final
            db.session.commit()
            
            print("\n=== RESUMEN DE IMPORTACIÓN ===")
            print(f"Ventas importadas exitosamente: {ventas_importadas}")
            print(f"Monto total importado: ${total_monto:,.2f}")
            print("Las ventas han sido registradas en la base de datos.")
            
        except Exception as e:
            print(f"Error durante la importación: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    archivo_excel = "ventasenero25_parte2.xlsx"
    importar_ventas(archivo_excel)
