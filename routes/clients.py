from flask import Blueprint, jsonify, request
from models import db, Client

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/api/clients', methods=['GET'])
def get_clients():
    try:
        # Get search term from query parameters
        search = request.args.get('search', '').lower()
        
        # Base query
        query = Client.query
        
        # Apply search filter if provided
        if search:
            query = query.filter(
                db.or_(
                    Client.name.ilike(f'%{search}%'),
                    Client.email.ilike(f'%{search}%'),
                    Client.phone.ilike(f'%{search}%'),
                    Client.rfc.ilike(f'%{search}%')
                )
            )
        
        # Get all clients
        clients = query.all()
        return jsonify([client.to_dict() for client in clients])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/api/clients', methods=['POST'])
def create_client():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'El nombre es requerido'}), 400
            
        # Check if email already exists
        if data.get('email'):
            existing_client = Client.query.filter_by(email=data['email']).first()
            if existing_client:
                return jsonify({'error': 'El email ya está registrado'}), 400
        
        # Create new client
        new_client = Client(
            name=data['name'],
            email=data.get('email'),
            phone=data.get('phone'),
            rfc=data.get('rfc'),
            address=data.get('address')
        )
        
        db.session.add(new_client)
        db.session.commit()
        
        return jsonify(new_client.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    try:
        client = Client.query.get_or_404(client_id)
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'El nombre es requerido'}), 400
            
        # Check if email already exists (if email is being updated)
        if data.get('email') and data['email'] != client.email:
            existing_client = Client.query.filter_by(email=data['email']).first()
            if existing_client:
                return jsonify({'error': 'El email ya está registrado'}), 400
        
        # Update fields
        client.name = data['name']
        if 'email' in data:
            client.email = data['email']
        if 'phone' in data:
            client.phone = data['phone']
        if 'rfc' in data:
            client.rfc = data['rfc']
        if 'address' in data:
            client.address = data['address']
        
        db.session.commit()
        return jsonify(client.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    try:
        client = Client.query.get_or_404(client_id)
        
        # Check if client has associated sales
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
