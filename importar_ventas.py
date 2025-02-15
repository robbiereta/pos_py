from app import create_app
from models import db, Sale, Client
import pandas as pd
from datetime import datetime

def importar_ventas(archivo_excel):
    # Crear la aplicación y el contexto
    app = create_app()
    
    with app.app_context():
        try:
            # Leer el archivo Excel
            df = pd.read_excel(archivo_excel)
            
            # Contador de ventas importadas
            ventas_importadas = 0
            total_monto = 0
            
            # Obtener o crear un cliente por defecto
            cliente_default = Client.query.filter_by(name='Cliente General').first()
            if not cliente_default:
                cliente_default = Client(
                    name='Cliente General',
                    email='general@example.com',
                    phone='0000000000'
                )
                db.session.add(cliente_default)
                db.session.commit()
            
            print("\nIniciando importación de ventas...")
            
            # Procesar cada venta
            for _, row in df.iterrows():
                try:
                    # Crear objeto de venta
                    venta = Sale(
                        date=datetime.strptime(row['fecha'], '%Y-%m-%d'),
                        total_amount=float(row['total_amount']),
                        amount_received=float(row['total_amount']),  # Asumimos pago exacto
                        change_amount=0.0,  # Sin cambio
                        client_id=cliente_default.id,
                        is_invoiced=False
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
    archivo_excel = "ventas_feb25_convertidas.xlsx"
    importar_ventas(archivo_excel)
