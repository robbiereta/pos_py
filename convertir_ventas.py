import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)

    try:
        # Configure MongoDB
        mongodb_uri = os.getenv("MONGODB_URI_DEVELOPMENT")    
        if not mongodb_uri:
            raise ValueError("MONGODB_URI_DEVELOPMENT not found in environment variables")
        
        # Initialize MongoDB using PyMongo directly
        client = MongoClient(mongodb_uri)
        db = client['pos_db']  # Use explicit database name
        
        # Test connection
        client.server_info()
        
        # Store mongo instance in app
        app.mongo_client = client
        app.db = db
        
        return app
        
    except Exception as e:
        print(f"Error initializing MongoDB: {str(e)}")
        raise

def convertir_e_importar_ventas(archivo_origen):
    # Crear la aplicación y el contexto
    app = create_app()
    
    with app.app_context():
        try:
            # Obtener la conexión a MongoDB
            if not hasattr(app, 'db') or app.db is None:
                raise ValueError("MongoDB connection not properly initialized")
            
            db = app.db
            
            # Leer el archivo de ventas original
            df = pd.read_excel(archivo_origen)
            
            # Estadísticas
            ventas_por_dia = defaultdict(float)
            total_ventas = 0
            min_venta = float('inf')
            max_venta = 0
            ventas_importadas = 0
            
            # Obtener o crear cliente por defecto
            cliente_default = db.clients.find_one({"name": "Cliente General"})
            if not cliente_default:
                cliente_default = {
                    "name": "Cliente General",
                    "email": "general@example.com",
                    "phone": "0000000000"
                }
                result = db.clients.insert_one(cliente_default)
                cliente_default['_id'] = result.inserted_id

            # Obtener o crear producto por defecto
            producto_default = db.products.find_one({"name": "Venta General"})
            if not producto_default:
                producto_default = {
                    "name": "Venta General",
                    "description": "Venta sin producto específico",
                    "price": 0.0,
                    "stock": 999999
                }
                result = db.products.insert_one(producto_default)
                producto_default['_id'] = result.inserted_id
            
            print("\nIniciando procesamiento de ventas...")
            
            # Procesar cada columna (día)
            for col in df.columns:
                print(f"Procesando columna: {col}, Total filas: {len(df[col])}")
                if len(df[col]) < 1:
                    print(f"Columna {col} está vacía, saltando...")
                    continue
                
                try:
                    fecha_str = df.iloc[0][col]
                    print(f"Fecha en primera fila de columna {col}: {fecha_str}")
                    
                    if pd.notna(fecha_str):
                        try:
                            # Convertir la fecha a datetime
                            if isinstance(fecha_str, str):
                                fecha = datetime.strptime(fecha_str.split()[0], '%d-%m-%Y')
                            else:
                                # Ensure fecha_str is a datetime object
                                if isinstance(fecha_str, datetime):
                                    fecha = fecha_str.replace(hour=0, minute=0, second=0, microsecond=0)
                                else:
                                    print(f"Error: fecha_str is not a datetime object: {fecha_str}")
                                    continue
                            
                            # Obtener todas las ventas de ese día (ignorando NaN)
                            ventas_dia = df[col][1:].dropna()
                            print(f"Ventas encontradas en columna {col}: {len(ventas_dia)}")
                            
                            for idx, venta_str in enumerate(ventas_dia):
                                print(f"Procesando venta {idx+1} en columna {col}: {venta_str}")
                                try:
                                    # Convertir la venta a float, eliminando el tiempo si existe
                                    if isinstance(venta_str, str):
                                        monto_str = venta_str.split()[0] if ' ' in venta_str else venta_str
                                    else:
                                        monto_str = str(venta_str)
                                    
                                    monto_float = float(monto_str)
                                    
                                    if monto_float > 0:
                                        # Todas las ventas son en efectivo
                                        metodo_pago = 'efectivo'
                                        
                                        # Crear la venta
                                        venta = {
                                            'timestamp': fecha,
                                            'amount': str(monto_float),
                                            'payment_method': metodo_pago,
                                            'client_id': str(cliente_default['_id']),
                                            'products': [str(producto_default['_id'])]
                                        }
                                        
                                        # Guardar en MongoDB
                                        db.sales.insert_one(venta)
                                        
                                        # Actualizar estadísticas
                                        fecha_key = fecha.strftime('%Y-%m-%d')
                                        ventas_por_dia[fecha_key] += monto_float
                                        total_ventas += monto_float
                                        min_venta = min(min_venta, monto_float)
                                        max_venta = max(max_venta, monto_float)
                                        ventas_importadas += 1
                                        
                                        if ventas_importadas % 100 == 0:
                                            print(f"Procesadas {ventas_importadas} ventas...")
                                            
                                except (ValueError, TypeError) as e:
                                    print(f"Error al procesar monto en columna {col}, venta {idx+1}: {venta_str} - {str(e)}")
                                    continue
                            
                        except (ValueError, TypeError) as e:
                            print(f"Error al procesar fecha en columna {col}: {fecha_str} - {str(e)}")
                            continue
                except Exception as e:
                    print(f"Error al acceder a datos en columna {col}: {str(e)}")
                    continue
            
            # Imprimir resumen
            print("\nResumen de importación:")
            print(f"Total de ventas importadas: {ventas_importadas}")
            print(f"Monto total: ${total_ventas:,.2f}")
            if ventas_importadas > 0:
                print(f"Venta mínima: ${min_venta:,.2f}")
                print(f"Venta máxima: ${max_venta:,.2f}")
            
            print("\nVentas por día:")
            for fecha, monto in ventas_por_dia.items():
                print(f"{fecha}: ${monto:,.2f}")
            
            return {'status': 'success'}
            
        except Exception as e:
            print(f"Error durante la importación: {str(e)}")
            return {'status': 'error'}

if __name__ == "__main__":
    archivo_origen = "ventas_abril_2quin.xlsx"
    resultado = convertir_e_importar_ventas(archivo_origen)
    print(f"\nEstado final: {resultado['status']}")
