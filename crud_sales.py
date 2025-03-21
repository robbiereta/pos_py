from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import ObjectId
import os
from models import Sale, SaleDetail
import traceback

# Initialize Flask app
app = Flask(__name__)

# Configure MongoDB
mongodb_uri = os.getenv('MONGODB_URI')
client = MongoClient(mongodb_uri)
db = client['pos_db']
sales_collection = db['sales']
sale_details_collection = db['sale_details']

@app.route('/api/sales', methods=['POST'])
def create_sale():
    try:
        sale_data = request.json
        client_id = sale_data.get('client_id')
        total_amount = sale_data.get('total_amount')
        amount_received = sale_data.get('amount_received')
        change_amount = sale_data.get('change_amount')
        details = sale_data.get('details')

        sale = Sale.create_sale(db, client_id, total_amount, amount_received, change_amount, details)
        sale['_id'] = str(sale['_id'])
        sale['client_id'] = str(sale['client_id'])
        return jsonify(sale), 201
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/sales', methods=['GET'])
def get_sales():
    try:
        sales = list(sales_collection.find())
        for sale in sales:
            sale['_id'] = str(sale['_id'])
            sale['client_id'] = str(sale['client_id'])
        return jsonify(sales), 200
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/sales/<id>', methods=['GET'])
def get_sale(id):
    try:
        sale = sales_collection.find_one({'_id': ObjectId(id)})
        if sale:
            sale['_id'] = str(sale['_id'])
            sale['client_id'] = str(sale['client_id'])
            return jsonify(sale), 200
        return jsonify({'error': 'Sale not found'}), 404
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/sales/<id>', methods=['PUT'])
def update_sale(id):
    try:
        update_data = request.json
        result = sales_collection.update_one({'_id': ObjectId(id)}, {'$set': update_data})
        if result.modified_count:
            return jsonify({'status': 'Sale updated'}), 200
        return jsonify({'error': 'Sale not found'}), 404
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/sales/<id>', methods=['DELETE'])
def delete_sale(id):
    try:
        result = sales_collection.delete_one({'_id': ObjectId(id)})
        if result.deleted_count:
            return jsonify({'status': 'Sale deleted'}), 200
        return jsonify({'error': 'Sale not found'}), 404
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        app.run(debug=True, port=5001)
    finally:
        client.close()
