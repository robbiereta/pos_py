import pandas as pd
import json
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask
from pymongo import MongoClient
from models import Sale, Client, SaleDetail, Product
import os
from dotenv import load_dotenv
from config import config

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    try:
        # Configure MongoDB
        mongodb_uri = os.getenv("MONGODB_URI")    
        if not mongodb_uri:
            raise ValueError("MONGODB_URI not found in environment variables")
        
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
            
            # Obtener las fechas de la primera fila
            fechas = df.iloc[0]
            
            # Estadísticas
            ventas_por_dia = defaultdict(float)
            total_ventas = 0
            min_venta = float('inf')
            max_venta = 0
            ventas_importadas = 0
            
            # Obtener o crear cliente por defecto
            cliente_default = db.clients.find_one({"name": "Cliente General"})
            if not cliente_default:
                cliente_default = Client.create_client(
                    db,
                    name="Cliente General",
                    email="general@example.com",
                    phone="0000000000"
                )

            # Obtener o crear producto por defecto
            producto_default = db.products.find_one({"name": "Venta General"})
            if not producto_default:
                producto_default = Product.create_product(
                    db,
                    name="Venta General",
                    description="Venta sin producto específico",
                    price=0.0,
                    stock=999999
                )
            
            print("\nIniciando procesamiento de ventas...")
            
            # Procesar cada columna (día)
            for col in df.columns:
                fecha_str = df.iloc[0][col]
                if isinstance(fecha_str, datetime):  # Si es una fecha válida
                    # Obtener todas las ventas de ese día (ignorando NaN)
                    montos = df.iloc[1:][col].dropna()
                    
                    # Crear una venta por cada monto
                    for monto in montos:
                        try:
                            monto_float = float(str(monto).replace(',', ''))
                            if monto_float > 0:  # Solo procesar montos positivos
                                # Crear venta
                                venta = Sale.create_sale(
                                    db,
                                    client_id=cliente_default['_id'],
                                    total_amount=monto_float,
                                    amount_received=monto_float,
                                    change_amount=0.0,
                                    details=[{
                                        'product_id': producto_default['_id'],
                                        'quantity': 1,
                                        'price': monto_float
                                    }],
                                    date=fecha_str  # Pasar la fecha del Excel
                                )
                                
                                # Actualizar estadísticas
                                fecha_key = fecha_str.strftime('%Y-%m-%d')
                                ventas_por_dia[fecha_key] += monto_float
                                total_ventas += monto_float
                                min_venta = min(min_venta, monto_float)
                                max_venta = max(max_venta, monto_float)
                                ventas_importadas += 1
                                
                                if ventas_importadas % 100 == 0:
                                    print(f"Procesadas {ventas_importadas} ventas...")
                                    
                        except (ValueError, TypeError) as e:
                            print(f"Error al procesar monto: {monto} - {str(e)}")
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
    archivo_origen = "ventasfeb25_3semana.xlsx"
    resultado = convertir_e_importar_ventas(archivo_origen)
    print(f"\nEstado final: {resultado['status']}")
