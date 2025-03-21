from flask import Flask, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from convertir_ventas import create_app
from corte_caja_mongo import CorteCajaMongo
from datetime import datetime
from bson import ObjectId
import json
from cfdi_generator import CFDIGenerator
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin

app = create_app()
app.secret_key = 'your_secret_key_here'  # Set a secret key for session management
CORS(app)  # Enable CORS for all routes

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

@app.route('/api/ventas', methods=['GET'])
def get_ventas():
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        query = {}
        if fecha_inicio and fecha_fin:
            query['timestamp'] = {
                '$gte': datetime.fromisoformat(fecha_inicio),
                '$lte': datetime.fromisoformat(fecha_fin)
            }
        
        ventas = list(app.db.sales.find(query).sort('timestamp', -1))
        ventas_json = json.dumps(ventas, cls=JSONEncoder)
        return app.response_class(ventas_json, content_type='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ventas', methods=['POST'])
def crear_venta():
    try:
        venta = request.json
        venta['timestamp'] = datetime.fromisoformat(venta['timestamp'])
        result = app.db.sales.insert_one(venta)
        return jsonify({'id': str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        totales = cortes.calcular_totales_del_mes(anio, mes)
        return jsonify(totales)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cfdi', methods=['GET'])
def get_cfdi():
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        query = {}
        if fecha_inicio and fecha_fin:
            query['fecha'] = {
                '$gte': datetime.fromisoformat(fecha_inicio),
                '$lte': datetime.fromisoformat(fecha_fin)
            }
        
        cfdi = list(app.db.cfdi.find(query).sort('fecha', -1))
        cfdi_json = json.dumps(cfdi, cls=JSONEncoder)
        return app.response_class(cfdi_json, content_type='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cfdi', methods=['POST'])
def crear_cfdi():
    try:
        cfdi_data = request.json
        cfdi_data['fecha'] = datetime.fromisoformat(cfdi_data['fecha'])
        result = app.db.cfdi.insert_one(cfdi_data)
        return jsonify({'id': str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nominas', methods=['GET'])
def get_nominas():
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        query = {}
        if fecha_inicio and fecha_fin:
            query['fecha_pago'] = {
                '$gte': datetime.fromisoformat(fecha_inicio),
                '$lte': datetime.fromisoformat(fecha_fin)
            }
        
        nominas = list(app.db.nominas.find(query).sort('fecha_pago', -1))
        nominas_json = json.dumps(nominas, cls=JSONEncoder)
        return app.response_class(nominas_json, content_type='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nominas', methods=['POST'])
def crear_nomina():
    try:
        nomina_data = request.json
        nomina_data['fecha_pago'] = datetime.fromisoformat(nomina_data['fecha_pago'])
        result = app.db.nominas.insert_one(nomina_data)
        return jsonify({'id': str(result.inserted_id)}), 201
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

@app.route('/api/generate_nomina', methods=['POST'])
def generate_nomina():
    try:
        # Get payroll (nómina) data from the request
        nomina_data = request.json
       
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

@app.route('/home')
def home():
    return "Welcome to the home page!"

if __name__ == '__main__':
    app.run(debug=True, port=5003)
