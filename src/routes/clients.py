from flask import Blueprint, request, jsonify
from src.core.models import Client
from src.core.db import db

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/api/clients', methods=['GET'])
def get_clients():
    clients = Client.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'rfc': c.rfc,
        'email': c.email,
        'address': c.address,
        'phone': c.phone
    } for c in clients])

@clients_bp.route('/api/clients', methods=['POST'])
def create_client():
    data = request.json
    try:
        client = Client(
            name=data['name'],
            rfc=data['rfc'],
            email=data.get('email'),
            address=data.get('address'),
            phone=data.get('phone')
        )
        db.session.add(client)
        db.session.commit()
        return jsonify({
            'id': client.id,
            'message': 'Cliente creado exitosamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@clients_bp.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    data = request.json
    try:
        client = Client.query.get_or_404(client_id)
        client.name = data.get('name', client.name)
        client.rfc = data.get('rfc', client.rfc)
        client.email = data.get('email', client.email)
        client.address = data.get('address', client.address)
        client.phone = data.get('phone', client.phone)
        db.session.commit()
        return jsonify({'message': 'Cliente actualizado exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@clients_bp.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    try:
        client = Client.query.get_or_404(client_id)
        db.session.delete(client)
        db.session.commit()
        return jsonify({'message': 'Cliente eliminado exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
