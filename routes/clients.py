from flask import Blueprint, jsonify, request, current_app
from models import Client
from bson import ObjectId
from datetime import datetime

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/api/clients', methods=['GET'])
def get_clients():
    try:
        search = request.args.get('search', '').lower()
        db = current_app.db
        
        # Construir la consulta
        query = {}
        if search:
            query = {
                "$or": [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}},
                    {"phone": {"$regex": search, "$options": "i"}},
                    {"rfc": {"$regex": search, "$options": "i"}}
                ]
            }
        
        # Obtener clientes
        clients = list(db.clients.find(query))
        
        # Convertir ObjectId a string para serialización JSON
        for client in clients:
            client['_id'] = str(client['_id'])
        
        return jsonify(clients)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/api/clients/<client_id>', methods=['GET'])
def get_client(client_id):
    try:
        db = current_app.db
        client = db.clients.find_one({"_id": ObjectId(client_id)})
        
        if not client:
            return jsonify({'error': 'Cliente no encontrado'}), 404
            
        client['_id'] = str(client['_id'])
        return jsonify(client)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/api/clients', methods=['POST'])
def create_client():
    try:
        data = request.get_json()
        db = current_app.db
        
        # Validar datos requeridos
        if not data.get('name'):
            return jsonify({'error': 'El nombre es requerido'}), 400
            
        # Verificar si ya existe un cliente con el mismo email o RFC
        if data.get('email'):
            existing_client = db.clients.find_one({"email": data['email']})
            if existing_client:
                return jsonify({'error': 'Ya existe un cliente con ese email'}), 400
                
        if data.get('rfc'):
            existing_client = db.clients.find_one({"rfc": data['rfc']})
            if existing_client:
                return jsonify({'error': 'Ya existe un cliente con ese RFC'}), 400
        
        # Crear nuevo cliente
        client = Client.create_client(
            db,
            name=data['name'],
            email=data.get('email'),
            phone=data.get('phone'),
            rfc=data.get('rfc'),
            address=data.get('address')
        )
        
        client['_id'] = str(client['_id'])
        return jsonify(client), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/api/clients/<client_id>', methods=['PUT'])
def update_client(client_id):
    try:
        data = request.get_json()
        db = current_app.db
        
        # Verificar si el cliente existe
        client = db.clients.find_one({"_id": ObjectId(client_id)})
        if not client:
            return jsonify({'error': 'Cliente no encontrado'}), 404
            
        # Verificar duplicados de email y RFC
        if data.get('email'):
            existing_client = db.clients.find_one({
                "_id": {"$ne": ObjectId(client_id)},
                "email": data['email']
            })
            if existing_client:
                return jsonify({'error': 'Ya existe otro cliente con ese email'}), 400
                
        if data.get('rfc'):
            existing_client = db.clients.find_one({
                "_id": {"$ne": ObjectId(client_id)},
                "rfc": data['rfc']
            })
            if existing_client:
                return jsonify({'error': 'Ya existe otro cliente con ese RFC'}), 400
        
        # Actualizar cliente
        update_data = {
            "name": data.get('name', client['name']),
            "email": data.get('email', client.get('email')),
            "phone": data.get('phone', client.get('phone')),
            "rfc": data.get('rfc', client.get('rfc')),
            "address": data.get('address', client.get('address')),
            "updated_at": datetime.utcnow()
        }
        
        db.clients.update_one(
            {"_id": ObjectId(client_id)},
            {"$set": update_data}
        )
        
        # Obtener cliente actualizado
        updated_client = db.clients.find_one({"_id": ObjectId(client_id)})
        updated_client['_id'] = str(updated_client['_id'])
        
        return jsonify(updated_client)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/api/clients/<client_id>', methods=['DELETE'])
def delete_client(client_id):
    try:
        db = current_app.db
        
        # Verificar si el cliente existe
        client = db.clients.find_one({"_id": ObjectId(client_id)})
        if not client:
            return jsonify({'error': 'Cliente no encontrado'}), 404
            
        # Verificar si el cliente tiene ventas asociadas
        sales = db.sales.find_one({"client_id": ObjectId(client_id)})
        if sales:
            return jsonify({'error': 'No se puede eliminar el cliente porque tiene ventas asociadas'}), 400
            
        # Eliminar cliente
        db.clients.delete_one({"_id": ObjectId(client_id)})
        
        return jsonify({'message': 'Cliente eliminado correctamente'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
