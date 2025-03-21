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
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import xml.etree.ElementTree as ET

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
            "price": 0.0,
            "nombre": "Producto de prueba"
        }
    ],
    "fecha": datetime.now().strftime("%Y-%m-%d"),    
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
            cliente = db.clients.find_one({"name": nota_venta["cliente"]["name_cliente"]})
            if not cliente:
                cliente = Client.create_client(
                    db,
                    name=nota_venta["cliente"]["name_cliente"],
                    phone=nota_venta["cliente"]["phone"],
                    rfc=nota_venta["cliente"]["rfc"],
                    address=nota_venta["cliente"]["address"]
                )

            # Obtener  productos
            lineas_venta = nota_venta["lineas_venta"]
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
                'timestamp': nota_venta["fecha"],
                'amount': nota_venta["total"],
                'payment_method': nota_venta["metodo_pago"],
                'client_id': str(cliente["_id"]),
                'products': lineas_venta
            }
                                    
            # Guardar en MongoDB
            result = db.sales.insert_one(venta)
                                    
            if (result.inserted_id):
                print("Venta guardada exitosamente")
                generar_factura(nota_venta["cliente"], nota_venta["lineas_venta"], nota_venta["total"], nota_venta["fecha"])
                return {'status': 'success', 'message': 'Venta guardada exitosamente'}
        except Exception as e:
            print(f"Error al guardar la venta: {str(e)}")
            return {'status': 'error', 'message': str(e)}
         
def guardar_cfdi(cfdi_data):
    app = create_app()
    with app.app_context():
        try:
            db = app.db
            cfdi = {
                'emisor': cfdi_data['emisor'],
                'receptor': cfdi_data['receptor'],
                'fecha': cfdi_data['fecha'],
                'total': cfdi_data['total'],
                'uuid': cfdi_data['uuid'],
                'xml': cfdi_data['xml'],
                'pdf': None
            }
            result = db.cfdi.insert_one(cfdi)
            if result.inserted_id:
                print("CFDI guardado exitosamente")
                generar_cfdi_pdf(cfdi)
                return {'status': 'success', 'message': 'CFDI guardado exitosamente'}
        except Exception as e:
            print(f"Error al guardar CFDI: {str(e)}")
            return {'status': 'error', 'message': str(e)}


def generar_xml_nomina(nomina_data):
    # Create the root element with namespaces
    root = ET.Element('cfdi:Comprobante', {
        'xmlns:cfdi': 'http://www.sat.gob.mx/cfd/3',
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsi:schemaLocation': 'http://www.sat.gob.mx/cfd/3 http://www.sat.gob.mx/sitio_internet/cfd/3/cfdv33.xsd',
        'Version': '3.3',
        'Serie': 'A',
        'Folio': '1',
        'Fecha': nomina_data['fecha_pago'],
        'FormaPago': '99',
        'NoCertificado': '00001000000403258748',
        'Certificado': '',
        'SubTotal': str(nomina_data['percepciones']),
        'Descuento': str(nomina_data['deducciones']),
        'Moneda': 'MXN',
        'Total': str(nomina_data['total']),
        'TipoDeComprobante': 'N',
        'MetodoPago': 'PUE',
        'LugarExpedicion': '45000'
    })

    # Add Emisor
    emisor = ET.SubElement(root, 'cfdi:Emisor', {
        'Rfc': nomina_data['empleado']['rfc'],
        'Nombre': nomina_data['empleado']['nombre'],
        'RegimenFiscal': '601'
    })

    # Add Receptor
    receptor = ET.SubElement(root, 'cfdi:Receptor', {
        'Rfc': 'XAXX010101000',
        'Nombre': 'Publico en General',
        'UsoCFDI': 'G03'
    })

    # Add Conceptos
    conceptos = ET.SubElement(root, 'cfdi:Conceptos')
    concepto = ET.SubElement(conceptos, 'cfdi:Concepto', {
        'ClaveProdServ': '84111505',
        'Cantidad': '1',
        'ClaveUnidad': 'ACT',
        'Descripcion': 'Pago de nómina',
        'ValorUnitario': str(nomina_data['percepciones']),
        'Importe': str(nomina_data['percepciones'])
    })

    # Convert to string
    xml_str = ET.tostring(root, encoding='utf-8').decode('utf-8')
    return xml_str

# Example usage
nomina_data_example = {
    "empleado": {"nombre": "Empleado Ejemplo", "rfc": "XAXX010101000"},
    "fecha_pago": "2025-03-18T10:00:00",
    "percepciones": 1000.0,
    "deducciones": 200.0,
    "total": 800.0
}
xml_output = generar_xml_nomina(nomina_data_example)
print(xml_output)

if __name__ == "__main__":
    nota_venta["total"] = nota_venta["lineas_venta"][0]["price"] * nota_venta["lineas_venta"][0]["quantity"]
    resultado = guardar_venta(nota_venta)
    print(f"\nEstado final: {resultado['status']}")
