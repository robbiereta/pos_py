from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import ObjectId
import os
from models import Client
import traceback

# Initialize Flask app
app = Flask(__name__)

# Configure MongoDB
mongodb_uri = os.getenv('MONGODB_URI')
client = MongoClient(mongodb_uri)
db = client['pos_db']
clients_collection = db['clients']

@app.route('/api/clients', methods=['POST'])
def create_client():
    try:
        client_data = request.json
        name = client_data.get('name')
        email = client_data.get('email')
        phone = client_data.get('phone')
        rfc = client_data.get('rfc')
        address = client_data.get('address')

        client = Client.create_client(db, name, email, phone, rfc, address)
        client['_id'] = str(client['_id'])
        return jsonify(client), 201
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/clients', methods=['GET'])
def get_clients():
    try:
        clients = list(clients_collection.find())
        for client in clients:
            client['_id'] = str(client['_id'])
        return jsonify(clients), 200
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/clients/<id>', methods=['GET'])
def get_client(id):
    try:
        client = clients_collection.find_one({'_id': ObjectId(id)})
        if client:
            client['_id'] = str(client['_id'])
            return jsonify(client), 200
        return jsonify({'error': 'Client not found'}), 404
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/clients/<id>', methods=['PUT'])
def update_client(id):
    try:
        update_data = request.json
        result = clients_collection.update_one({'_id': ObjectId(id)}, {'$set': update_data})
        if result.modified_count:
            return jsonify({'status': 'Client updated'}), 200
        return jsonify({'error': 'Client not found'}), 404
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/clients/<id>', methods=['DELETE'])
def delete_client(id):
    try:
        result = clients_collection.delete_one({'_id': ObjectId(id)})
        if result.deleted_count:
            return jsonify({'status': 'Client deleted'}), 200
        return jsonify({'error': 'Client not found'}), 404
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        app.run(debug=True, port=5002)
    finally:
        client.close()
