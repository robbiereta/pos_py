import pandas as pd
from app import create_app
from models import db, Sale
import json
from datetime import datetime

def importar_ventas(archivo_ventas):
    app = create_app()
    
    with app.app_context():
        try:
            # Leer el archivo de ventas convertidas
            df = pd.read_excel(archivo_ventas)
            
            # Contador de ventas importadas
            ventas_importadas = 0
            total_monto = 0
            
            print(f"\nIniciando importación de {len(df)} ventas...")
            
            # Procesar cada venta
            for _, row in df.iterrows():
                try:
                    # Convertir fecha a datetime
                    fecha = datetime.strptime(row['fecha'], '%Y-%m-%d')
                    
                    # Crear nueva venta
                    venta = Sale(
                        timestamp=fecha,
                        total_amount=float(row['total_amount']),
                        products=row['products'],
                        is_invoiced=False
                    )
                    
                    # Agregar a la base de datos
                    db.session.add(venta)
                    ventas_importadas += 1
                    total_monto += float(row['total_amount'])
                    
                    # Commit cada 50 ventas para evitar problemas de memoria
                    if ventas_importadas % 50 == 0:
                        db.session.commit()
                        print(f"- Importadas {ventas_importadas} ventas...")
                
                except Exception as e:
                    print(f"Error al importar venta: {str(e)}")
                    print(f"Datos de la venta: {row.to_dict()}")
                    continue
            
            # Commit final
            db.session.commit()
            
            print("\n=== RESUMEN DE IMPORTACIÓN ===")
            print(f"Total de ventas importadas: {ventas_importadas}")
            print(f"Monto total importado: ${total_monto:,.2f}")
            print(f"Promedio por venta: ${total_monto/ventas_importadas:,.2f}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\nError durante la importación: {str(e)}")
            print("Se ha revertido la operación.")

if __name__ == "__main__":
    archivo_ventas = "ventas_enero_parte2_convertidas.xlsx"
    importar_ventas(archivo_ventas)
