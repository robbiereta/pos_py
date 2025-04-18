from flask import Flask, jsonify, request, Blueprint
from pymongo import MongoClient
from bson import ObjectId
import os
from models import Sale, Invoice, GlobalInvoice, NominaInvoice
import traceback
from datetime import datetime
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)
# Configure MongoDB
mongodb_uri = os.getenv('MONGODB_URI')
client = MongoClient(mongodb_uri)
db = client['pos_db']
sales_collection = db['sales']
sale_details_collection = db['sale_details']
cfdi_collection = db['cfdi']            
invoice_collection = db['invoices']
global_invoice_collection = db['global_invoices']
nomina_invoice_collection = db['nomina_invoices']

# Initialize Flask Blueprint
sales_app = Blueprint('sales_app', __name__)

@sales_app.route('/', methods=['POST'])
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

@sales_app.route('/', methods=['GET'])
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

@sales_app.route('/<id>', methods=['GET'])
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

@sales_app.route('/<id>', methods=['PUT'])
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

@sales_app.route('/<id>', methods=['DELETE'])
def delete_sale(id):
    try:
        result = sales_collection.delete_one({'_id': ObjectId(id)})
        if result.deleted_count:
            return jsonify({'status': 'Sale deleted'}), 200
        return jsonify({'error': 'Sale not found'}), 404
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@sales_app.route('/api/cfdi/from_sales', methods=['POST'])
def create_cfdi_from_sales():
    try:
        sales_ids = request.json.get('sales_ids')
        sales = list(sales_collection.find({'_id': {'$in': [ObjectId(sid) for sid in sales_ids]}}))

        if not sales:
            return jsonify({'error': 'No sales found'}), 404

        # Example: Generate CFDI content
        cfdi_content = f"CFDI for sales: {', '.join([str(s['_id']) for s in sales])}"

        # Store the CFDI in the database
        cfdi_id = cfdi_collection.insert_one({'content': cfdi_content, 'sales_ids': sales_ids}).inserted_id

        return jsonify({'cfdi_id': str(cfdi_id), 'message': 'CFDI created successfully'}), 201
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@sales_app.route('/api/cfdi/client', methods=['POST'])
def create_client_cfdi():
    try:
        data = request.json
        invoice = Invoice.create_invoice(db, data['sale_id'], data['cfdi_uuid'], data['xml_content'], datetime.now())
        return jsonify(invoice), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sales_app.route('/api/cfdi/global', methods=['POST'])
def create_global_cfdi():
    try:
        data = request.json
        global_invoice = GlobalInvoice.create_global_invoice(db, data['date'], data['total_amount'], data['tax_amount'], data['cfdi_uuid'], data['folio'], data['xml_content'], data['sale_ids'])
        return jsonify(global_invoice), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sales_app.route('/api/cfdi/nomina', methods=['POST'])
def create_nomina_cfdi():
    try:
        data = request.json
        nomina_invoice = NominaInvoice.create_nomina_invoice(db, data['employee_id'], data['cfdi_uuid'], data['xml_content'], datetime.now())
        return jsonify(nomina_invoice), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sales_app.route('/api/cfdi/<cfdi_id>', methods=['GET'])
def get_cfdi(cfdi_id):
    try:
        cfdi = cfdi_collection.find_one({'_id': ObjectId(cfdi_id)})
        if not cfdi:
            return jsonify({'error': 'CFDI not found'}), 404
        return jsonify(cfdi), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sales_app.route('/api/cfdi/<cfdi_id>', methods=['PUT'])
def update_cfdi(cfdi_id):
    try:
        update_data = request.json
        result = cfdi_collection.update_one({'_id': ObjectId(cfdi_id)}, {'$set': update_data})
        if result.modified_count:
            return jsonify({'status': 'CFDI updated'}), 200
        return jsonify({'error': 'CFDI not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sales_app.route('/api/cfdi/<cfdi_id>', methods=['DELETE'])
def delete_cfdi(cfdi_id):
    try:
        result = cfdi_collection.delete_one({'_id': ObjectId(cfdi_id)})
        if result.deleted_count:
            return jsonify({'status': 'CFDI deleted'}), 200
        return jsonify({'error': 'CFDI not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        app.register_blueprint(sales_app)
        app.run(debug=True, port=5001)
    finally:
        client.close()
