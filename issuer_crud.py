from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import ObjectId
import os

# Initialize Flask app
app = Flask(__name__)

# Configure MongoDB
mongodb_uri = os.getenv('MONGODB_URI')
client = MongoClient(mongodb_uri)
db = client['pos_db']
emisores_collection = db['emisores']

@app.route('/api/emisores', methods=['POST'])
def create_emitter():
    try:
        emitter_data = request.json
        result = emisores_collection.insert_one(emitter_data)
        return jsonify({'id': str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emisores', methods=['GET'])
def get_emisores():
    try:
        emisores = list(emisores_collection.find())
        for emitter in emisores:
            emitter['_id'] = str(emitter['_id'])
        return jsonify(emisores), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emisores/<id>', methods=['GET'])
def get_emitter(id):
    try:
        emitter = emisores_collection.find_one({'_id': ObjectId(id)})
        if emitter:
            emitter['_id'] = str(emitter['_id'])
            return jsonify(emitter), 200
        return jsonify({'error': 'Emitter not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emisores/<id>', methods=['PUT'])
def update_emitter(id):
    try:
        update_data = request.json
        result = emisores_collection.update_one({'_id': ObjectId(id)}, {'$set': update_data})
        if result.modified_count:
            return jsonify({'status': 'Emitter updated'}), 200
        return jsonify({'error': 'Emitter not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emisores/<id>', methods=['DELETE'])
def delete_emitter(id):
    try:
        result = emisores_collection.delete_one({'_id': ObjectId(id)})
        if result.deleted_count:
            return jsonify({'status': 'Emitter deleted'}), 200
        return jsonify({'error': 'Emitter not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
