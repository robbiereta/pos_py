from flask import Flask, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from convertir_ventas import create_app
from corte_caja_mongo import CorteCajaMongo
from datetime import datetime
from bson import ObjectId
import json
from cfdi_generator import CFDIGenerator
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import (  
    LoginManager,
    login_user,
    login_required,
    logout_user,
    UserMixin
)
import requests

# Import CRUD modules
from crud_sales import sales_app as sales_bp
from routes.clients import clients_bp
from issuer_crud import issuer_app as issuer_bp
from employee_crud import employee_app as employee_bp
from routes.products import products_bp

app = create_app()
app.secret_key = 'your_secret_key_here'  # Set a secret key for session management
# Configure CORS to allow requests from frontend
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})  # Enable CORS for frontend requests

# Register blueprints for CRUD operations
app.register_blueprint(sales_bp, url_prefix='/api/sales')
app.register_blueprint(clients_bp, url_prefix='/api/clients')
app.register_blueprint(issuer_bp, url_prefix='/api/issuer')
app.register_blueprint(employee_bp, url_prefix='/api/employee')
app.register_blueprint(products_bp, url_prefix='/api/products')
# Helper para convertir ObjectId a string
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

# Configurar el encoder personalizado
app.json_encoder = JSONEncoder

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Sample user data for demonstration
users = {
    "user1": {"password": generate_password_hash("hashed_password"), "role": "issuer"},
    "user2": {"password": generate_password_hash("hashed_password"), "role": "employee"}
}

# Define a User class
class User(UserMixin):
    def __init__(self, username, role):
        self.id = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    user = users.get(user_id)
    if user:
        return User(user_id, user['role'])
    return None


@app.route('/api/cortes', methods=['GET'])
def get_cortes():
    try:
        cortes = CorteCajaMongo(app.db)
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            inicio = datetime.fromisoformat(fecha_inicio)
            fin = datetime.fromisoformat(fecha_fin)
            resultados = cortes.obtener_cortes(inicio, fin)
        else:
            resultados = cortes.obtener_cortes()
            
        return jsonify(resultados)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cortes', methods=['POST'])
def crear_corte():
    try:
        data = request.json
        cortes = CorteCajaMongo(app.db)
        
        corte_id = cortes.crear_corte(
            monto_inicial=data['monto_inicial'],
            monto_final=data['monto_final'],
            ventas_efectivo=data.get('ventas_efectivo', 0),
            ventas_tarjeta=data.get('ventas_tarjeta', 0),
            ventas_transferencia=data.get('ventas_transferencia', 0),
            retiros=data.get('retiros', 0),
            notas=data.get('notas', '')
        )
        return jsonify({'id': corte_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cortes/<corte_id>', methods=['GET'])
def get_corte(corte_id):
    try:
        cortes = CorteCajaMongo(app.db)
        corte = cortes.obtener_corte(corte_id)
        if corte:
            return jsonify(corte)
        return jsonify({'error': 'Corte no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cortes/totales/<int:anio>/<int:mes>', methods=['GET'])
def get_totales_mes(anio, mes):
    try:
        cortes = CorteCajaMongo(app.db)
        totales = cortes.obtener_totales_mes(anio, mes)
        return jsonify(totales)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_cfdi', methods=['POST'])
def generate_cfdi():
    try:
        # Get the payroll data from the request
        nomina_data = request.json
        
        # Generate XML for CFDI 4.0
        xml_data = generar_xml_nomina_v4(nomina_data)
        
        # Certify the CFDI using SW's Sapien API
        generator = CFDIGenerator()
        certification_result = generator.certify_cfdi(xml_data)
        
        # Return the certification result
        if certification_result:
            return jsonify(certification_result), 200
        else:
            return jsonify({'error': 'Certification failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/login', methods=['POST'])
def login():
    try:
        username = request.json.get('username')
        password = request.json.get('password')

        user = users.get(username)
        if user and check_password_hash(user['password'], password):
            user_obj = User(username, user['role'])
            login_user(user_obj)
            return redirect(url_for('home'))
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    try:
        if session.get('role') == 'issuer':
            # Logic to get users
            return jsonify({'users': list(users.keys())})
        else:
            return jsonify({'error': 'Unauthorized'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        username = request.json.get('username')
        password = request.json.get('password')
        role = request.json.get('issuer')

        if username in users:
            return jsonify({'error': 'User already exists'}), 400

        hashed_password = generate_password_hash(password)
        users[username] = {'password': hashed_password, 'role': role}

        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mercadolibre/products', methods=['GET'])
def get_mercadolibre_products():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    url = f'https://api.mercadolibre.com/sites/MLA/search?q={query}'
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch data from MercadoLibre'}), response.status_code
    
    data = response.json()
    return jsonify(data), 200

@app.route('/api/generate_client_cfdi', methods=['POST'])
@login_required
def generate_client_cfdi(venta_data=None):
    try:
        if venta_data is None:
            data = request.json
        else:
            data = venta_data
        nota_venta = data.get('nota_venta')
        
        if not nota_venta:
            if venta_data is None:
                return jsonify({'error': 'Se requiere el ID de la nota de venta'}), 400
            else:
                return {'error': 'Se requiere el ID de la nota de venta'}
            
        app_instance = create_app()
        with app_instance.app_context():
            # Obtener venta específica por ID
            print(f"Buscando venta con ID: {nota_venta}, tipo: {type(nota_venta)}")
            sale = app_instance.db.sales.find_one({"_id": str(nota_venta)})
            
            if not sale:
                error_msg = f"No se encontró la venta con ID {nota_venta}"
                print(error_msg)
                if venta_data is None:
                    return jsonify({'error': error_msg}), 404
                else:
                    return {'error': error_msg}
            
            # Verificar si ya fue facturada
            if sale.get('facturada', False):
                if venta_data is None:
                    return jsonify({'error': 'Esta venta ya ha sido facturada'}), 400
                else:
                    return {'error': 'Esta venta ya ha sido facturada'}
                
            # Obtener información del cliente
            client_id = sale.get('client_id')
            client = app_instance.db.clients.find_one({"_id": client_id}) if client_id else None
            
            if not client:
                if venta_data is None:
                    return jsonify({'error': 'No se encontró información del cliente. No se puede generar factura'}), 404
                else:
                    return {'error': 'No se encontró información del cliente. No se puede generar factura'}
            
            # Calcular totales
            total_amount = sale.get('total_amount', 0)
            # El IVA ya está incluido en el total, así que lo extraemos (16%)
            subtotal = total_amount / 1.16
            tax_amount = total_amount - subtotal
            
            # Obtener fecha actual
            fecha_emision = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            
            # Preparar conceptos (productos) de la venta
            conceptos = []
            for item in sale.get('items', []):
                concepto = {
                    'ClaveProdServ': item.get('product_code', '01010101'),
                    'Cantidad': item.get('quantity', 1),
                    'ClaveUnidad': item.get('unit_code', 'H87'),
                    'Unidad': item.get('unit', 'Pieza'),
                    'Descripcion': item.get('description', 'Producto'),
                    'ValorUnitario': item.get('price', 0),
                    'Importe': item.get('total', 0),
                    'Descuento': item.get('discount', 0),
                    'ObjetoImp': '02',  # Objeto de impuesto
                    'Impuestos': {
                        'Traslados': [{
                            'Base': item.get('total', 0) / 1.16,
                            'Impuesto': '002',  # IVA
                            'TipoFactor': 'Tasa',
                            'TasaOCuota': '0.160000',
                            'Importe': item.get('total', 0) - (item.get('total', 0) / 1.16)
                        }]
                    }
                }
                conceptos.append(concepto)
            
            # Preparar datos para el CFDI
            cfdi_data = {
                'Serie': 'A',
                'Folio': str(nota_venta)[-6:],  # Últimos 6 dígitos del ID de venta
                'Fecha': fecha_emision,
                'FormaPago': sale.get('payment_method', '01'),  # 01 - Efectivo
                'MetodoPago': 'PUE',  # Pago en una sola exhibición
                'LugarExpedicion': '67100',  # Código postal
                'Receptor': {
                    'Rfc': client.get('rfc', 'XAXX010101000'),
                    'Nombre': client.get('name', 'PUBLICO EN GENERAL'),
                    'UsoCFDI': client.get('uso_cfdi', 'G03'),  # Gastos en general
                    'RegimenFiscalReceptor': client.get('regimen_fiscal', '616'),  # Sin obligaciones fiscales
                    'DomicilioFiscalReceptor': client.get('codigo_postal', '67100')
                },
                'Conceptos': conceptos,
                'Impuestos': {
                    'TotalImpuestosTrasladados': tax_amount,
                    'Traslados': [{
                        'Impuesto': '002',
                        'TipoFactor': 'Tasa',
                        'TasaOCuota': '0.160000',
                        'Importe': tax_amount
                    }]
                },
                'SubTotal': round(subtotal, 2),
                'Total': round(total_amount, 2)
            }
            
            # Generar CFDI
            generator = CFDIGenerator()
            xml_path = generator.generate_cfdi(cfdi_data, f"factura_{nota_venta}.xml")
            
            if xml_path:
                # Actualizar estado de la venta
                app_instance.db.sales.update_one(
                    {"_id": nota_venta},
                    {"$set": {"facturada": True, "fecha_factura": datetime.now()}}
                )
                if venta_data is None:
                    return jsonify({'success': True, 'message': 'Factura generada exitosamente', 'xml_path': xml_path}), 200
                else:
                    return {'success': True, 'message': 'Factura generada exitosamente', 'xml_path': xml_path}
            else:
                if venta_data is None:
                    return jsonify({'error': 'Error al generar la factura'}), 500
                else:
                    return {'error': 'Error al generar la factura'}
                
    except Exception as e:
        error_message = f"Error al generar factura: {str(e)}"
        if venta_data is None:
            return jsonify({'error': error_message}), 500
        else:
            return {'error': error_message}

@app.route('/api/facturar_venta', methods=['POST'])
@login_required
def facturar_venta():
    try:
        venta_data = request.json
        if not venta_data:
            return jsonify({'error': 'No se proporcionaron datos de la venta'}), 400

        # Validar datos necesarios para la factura
        required_fields = ['client_id', 'items']
        for field in required_fields:
            if field not in venta_data:
                return jsonify({'error': f'Falta el campo {field} en los datos de la venta'}), 400

        # Aquí puedes agregar más validaciones según tus necesidades
        # Por ejemplo, verificar si el cliente existe, si hay stock de los productos, etc.

        # Generar la factura CFDI pasando los datos de la venta
        cfdi_result = generate_client_cfdi(venta_data)

        if cfdi_result and 'error' not in cfdi_result:
            return jsonify({'message': 'Factura generada exitosamente', 'cfdi_data': cfdi_result}), 200
        else:
            return jsonify({'error': 'Error al generar la factura', 'details': cfdi_result.get('error', 'Unknown error')}), 500
    except Exception as e:
        return jsonify({'error': 'Error al procesar la facturación', 'details': str(e)}), 500

@app.route('/home')
def home():
    return "Welcome to the home page!"

if __name__ == '__main__':
    app.run(debug=True, port=5003)
