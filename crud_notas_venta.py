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
nota_venta = {
    "cliente":{
        "name_cliente": "fulano",
        "phone": "",
        "rfc": "",
        "address": ""
    },
    "lineas_venta": [
        {
            "product_id": "",
            "quantity": 1,
            "price": 0.0
        }
    ],
    "fecha": "",    
    "total": 0.0,
    "metodo_pago": "efectivo"
}

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

def guardar_venta(nota_venta):
    # Crear la aplicación y el contexto
    app = create_app()
    
    with app.app_context():
        try:
            # Obtener la conexión a MongoDB
            if not hasattr(app, 'db') or app.db is None:
                raise ValueError("MongoDB connection not properly initialized")
            
            db = app.db
            
       
            # Obtener o crear cliente por defecto
            cliente = db.clients.find_one({"name": nota_venta.cliente.name_cliente})
            if not cliente:
                cliente = Client.create_client(
                    db,
                    name=nota_venta.cliente.name_cliente,
                    phone=nota_venta.cliente.phone,
                    rfc=nota_venta.cliente.rfc,
                    address=nota_venta.cliente.address
                )

            # Obtener  productos
            lineas_venta = nota_venta.lineas_venta
            # if not producto:
            #     producto = Product.create_product(
            #         db,
            #         name="Venta General",
            #         description="Venta sin producto específico",
            #         price=0.0,
            #         stock=999999
            #     )
            
            print("\nIniciando procesamiento de ventas...")
            
       
            # Todas las ventas son en efectivo
            metodo_pago = 'efectivo'
            
            # Crear la venta
            venta = {
                'timestamp': nota_venta.fecha,
                'amount': nota_venta.total,
                'payment_method': nota_venta.metodo_pago,
                'client_id': str(cliente),
                'products': lineas_venta
            }
                                    
            # Guardar en MongoDB
            result = db.sales.insert_one(venta)
                                    
            if (result.inserted_id):
                print("Venta guardada exitosamente")
                return {'status': 'success', 'message': 'Venta guardada exitosamente'}
        except Exception as e:
            print(f"Error al guardar la venta: {str(e)}")
            return {'status': 'error', 'message': str(e)}
         
if __name__ == "__main__":
    resultado = guardar_venta(nota_venta)
    print(f"\nEstado final: {resultado['status']}")
