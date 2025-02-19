from flask import Blueprint, jsonify, request
from models import db, Client

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/api/clients', methods=['GET'])
def get_clients():
    try:
        search = request.args.get('search', '').lower()
        query = Client.query
        
        if search:
            query = query.filter(
                db.or_(
                    Client.name.ilike(f'%{search}%'),
                    Client.email.ilike(f'%{search}%'),
                    Client.phone.ilike(f'%{search}%'),
                    Client.rfc.ilike(f'%{search}%')
                )
            )
        
        clients = query.all()
        return jsonify([client.to_dict() for client in clients])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    try:
        client = Client.query.get_or_404(client_id)
        return jsonify(client.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/api/clients', methods=['POST'])
def create_client():
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('name'):
            return jsonify({'error': 'El nombre es requerido'}), 400
            
        # Verificar si ya existe un cliente con el mismo email o RFC
        if data.get('email'):
            existing_client = Client.query.filter_by(email=data['email']).first()
            if existing_client:
                return jsonify({'error': 'Ya existe un cliente con ese email'}), 400
                
        if data.get('rfc'):
            existing_client = Client.query.filter_by(rfc=data['rfc']).first()
            if existing_client:
                return jsonify({'error': 'Ya existe un cliente con ese RFC'}), 400
        
        # Crear nuevo cliente
        client = Client(
            name=data['name'],
            email=data.get('email'),
            phone=data.get('phone'),
            rfc=data.get('rfc'),
            address=data.get('address')
        )
        
        db.session.add(client)
        db.session.commit()
        
        return jsonify(client.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    try:
        client = Client.query.get_or_404(client_id)
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('name'):
            return jsonify({'error': 'El nombre es requerido'}), 400
            
        # Verificar si ya existe otro cliente con el mismo email o RFC
        if data.get('email') and data['email'] != client.email:
            existing_client = Client.query.filter_by(email=data['email']).first()
            if existing_client:
                return jsonify({'error': 'Ya existe un cliente con ese email'}), 400
                
        if data.get('rfc') and data['rfc'] != client.rfc:
            existing_client = Client.query.filter_by(rfc=data['rfc']).first()
            if existing_client:
                return jsonify({'error': 'Ya existe un cliente con ese RFC'}), 400
        
        # Actualizar cliente
        client.name = data['name']
        client.email = data.get('email')
        client.phone = data.get('phone')
        client.rfc = data.get('rfc')
        client.address = data.get('address')
        
        db.session.commit()
        
        return jsonify(client.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    try:
        client = Client.query.get_or_404(client_id)
        
        # Verificar si el cliente tiene ventas asociadas
        if client.sales:
            return jsonify({
                'error': 'No se puede eliminar el cliente porque tiene ventas asociadas'
            }), 400
        
        db.session.delete(client)
        db.session.commit()
        
        return jsonify({'message': 'Cliente eliminado correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
