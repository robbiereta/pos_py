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
            print(f"Leyendo archivo: {archivo_origen}")
            
            # Leer el archivo Excel sin asumir el formato
            df = pd.read_excel(archivo_origen)
            print("\nPrimeras filas del archivo:")
            print(df.head())
            
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
            
            print("\nIniciando procesamiento de ventas de Julio 2025...")
            
            # Primero, intentar encontrar la columna de fechas
            fecha_col = None
            total_col = None
            
            # Buscar columnas que parezcan contener fechas
            for col in df.columns:
                # Verificar si la columna parece contener fechas
                if df[col].dtype == 'datetime64[ns]':
                    fecha_col = col
                    print(f"Columna de fechas identificada: {fecha_col}")
                    break
                
                # Verificar si el nombre de la columna sugiere que contiene fechas
                if any(term in str(col).lower() for term in ['fecha', 'date', 'dia']):
                    fecha_col = col
                    print(f"Posible columna de fechas por nombre: {fecha_col}")
                    break
            
            # Si no encontramos una columna de fechas, asumir que la primera columna es la de fechas
            if fecha_col is None:
                fecha_col = df.columns[0]
                print(f"Usando primera columna como fecha: {fecha_col}")
            
            # Buscar columna de totales
            for col in df.columns:
                if any(term in str(col).lower() for term in ['total', 'monto', 'importe', 'amount']):
                    total_col = col
                    print(f"Columna de totales identificada: {total_col}")
                    break
            
            # Si no encontramos una columna de totales, usar la segunda columna
            if total_col is None and len(df.columns) > 1:
                total_col = df.columns[1]
                print(f"Usando segunda columna como total: {total_col}")
            
            # Procesar cada fila
            for idx, row in df.iterrows():
                try:
                    # Obtener la fecha de la fila actual
                    fecha_val = row[fecha_col]
                    
                    # Saltar filas sin fecha o con encabezados
                    if pd.isna(fecha_val) or fecha_val == 'Fecha' or fecha_val == 'Total':
                        continue
                    
                    # Convertir la fecha a datetime
                    try:
                        if isinstance(fecha_val, str):
                            # Intentar diferentes formatos de fecha
                            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', '%d-%m-%Y', '%m-%d-%Y'):
                                try:
                                    fecha = datetime.strptime(fecha_val, fmt)
                                    break
                                except ValueError:
                                    continue
                            else:
                                print(f"No se pudo parsear la fecha: {fecha_val}")
                                continue
                        else:
                            # Si es un objeto de fecha de pandas o similar
                            fecha = pd.to_datetime(fecha_val)
                    except Exception as e:
                        print(f"Error al convertir fecha {fecha_val}: {str(e)}")
                        continue
                    
                    # Verificar que la fecha sea de julio de 2025
                    if fecha.month != 7 or fecha.year != 2025:
                        print(f"Advertencia: La fecha {fecha.strftime('%Y-%m-%d')} no es de julio de 2025. Saltando...")
                        continue
                    
                    # Obtener el total de la venta
                    if total_col is None:
                        # Si no hay columna de totales, buscar la primera columna numérica
                        for col in df.columns:
                            if col != fecha_col and pd.api.types.is_numeric_dtype(df[col]):
                                total_col = col
                                break
                        
                        if total_col is None:
                            print("No se pudo encontrar una columna con montos de venta")
                            break
                    
                    valor = row[total_col]
                    
                    # Verificar que el valor sea un número válido
                    if pd.isna(valor) or not isinstance(valor, (int, float)) or valor <= 0:
                        continue
                    
                    try:
                        # Crear la venta
                        sale_data = {
                            'client_id': cliente_default['_id'],
                            'sale_date': fecha,
                            'subtotal': float(valor),
                            'tax': 0.0,
                            'total': float(valor),
                            'payment_method': 'Efectivo',
                            'status': 'completed',
                            'created_at': datetime.now(),
                            'updated_at': datetime.now()
                        }
                        
                        # Insertar la venta
                        result = db.sales.insert_one(sale_data)
                        
                        # Crear el detalle de la venta
                        sale_detail = {
                            'sale_id': result.inserted_id,
                            'product_id': producto_default['_id'],
                            'quantity': 1,
                            'price': float(valor),
                            'subtotal': float(valor),
                            'created_at': datetime.now(),
                            'updated_at': datetime.now()
                        }
                        
                        db.sale_details.insert_one(sale_detail)
                        
                        # Actualizar estadísticas
                        fecha_str = fecha.strftime('%Y-%m-%d')
                        ventas_por_dia[fecha_str] += float(valor)
                        total_ventas += float(valor)
                        min_venta = min(min_venta, float(valor))
                        max_venta = max(max_venta, float(valor))
                        ventas_importadas += 1
                        
                        if ventas_importadas % 10 == 0:
                            print(f"Ventas procesadas: {ventas_importadas}")
                        
                    except Exception as e:
                        print(f"Error al procesar venta en fila {idx+1}: {str(e)}")
                        print(f"Valor: {valor}, Tipo: {type(valor)}")
                        continue
                
                except Exception as e:
                    print(f"Error al procesar fila {idx+1}: {str(e)}")
                    continue
            
            # Generar reporte
            print("\n" + "="*50)
            print("REPORTE DE IMPORTACIÓN DE VENTAS - JULIO 2025")
            print("="*50)
            print(f"Total de ventas importadas: {ventas_importadas}")
            print(f"Monto total de ventas: ${total_ventas:,.2f}")
            print(f"Venta mínima: ${min_venta:,.2f}")
            print(f"Venta máxima: ${max_venta:,.2f}")
            print("\nVentas por día:")
            for fecha, total in sorted(ventas_por_dia.items()):
                print(f"  {fecha}: ${total:,.2f}")
            
            return {
                'status': 'success',
                'ventas_importadas': ventas_importadas,
                'total_ventas': total_ventas,
                'ventas_por_dia': dict(ventas_por_dia)
            }
            
        except Exception as e:
            print(f"Error general: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

if __name__ == "__main__":
    # Nombre del archivo de ventas de julio
    archivo_origen = "ventas_julio.xlsx"  # Archivo de ventas de julio
    
    print(f"Iniciando importación de ventas desde: {archivo_origen}")
    print("Asegúrate de que el archivo esté en el directorio actual.")
    
    # Verificar si el archivo existe
    if not os.path.exists(archivo_origen):
        print(f"Error: No se encontró el archivo {archivo_origen}")
        print("Por favor, asegúrate de que el archivo existe en el directorio actual.")
    else:
        resultado = convertir_e_importar_ventas(archivo_origen)
        print(f"\nEstado final: {resultado['status']}")
        if 'message' in resultado:
            print(f"Mensaje: {resultado['message']}")