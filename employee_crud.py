from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import ObjectId
import os
from convertir_ventas import create_app

# Initialize Flask app
app = create_app()

# Configure MongoDB
mongodb_uri = os.getenv('MONGODB_URI')
client = MongoClient(mongodb_uri)
db = client['pos_db']
employees_collection = db['employees']

@app.route('/api/employees', methods=['POST'])
def create_employee():
    try:
        employee_data = request.json
        result = employees_collection.insert_one(employee_data)
        return jsonify({'id': str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees', methods=['GET'])
def get_employees():
    try:
        employees = list(employees_collection.find())
        for employee in employees:
            employee['_id'] = str(employee['_id'])
        return jsonify(employees), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees/<id>', methods=['GET'])
def get_employee(id):
    try:
        employee = employees_collection.find_one({'_id': ObjectId(id)})
        if employee:
            employee['_id'] = str(employee['_id'])
            return jsonify(employee), 200
        return jsonify({'error': 'Employee not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees/<id>', methods=['PUT'])
def update_employee(id):
    try:
        update_data = request.json
        result = employees_collection.update_one({'_id': ObjectId(id)}, {'$set': update_data})
        if result.modified_count:
            return jsonify({'status': 'Employee updated'}), 200
        return jsonify({'error': 'Employee not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees/<id>', methods=['DELETE'])
def delete_employee(id):
    try:
        result = employees_collection.delete_one({'_id': ObjectId(id)})
        if result.deleted_count:
            return jsonify({'status': 'Employee deleted'}), 200
        return jsonify({'error': 'Employee not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
