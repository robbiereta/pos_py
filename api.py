from flask import Flask, jsonify, request
from flask_cors import CORS
from convertir_ventas import create_app
from corte_caja_mongo import CorteCajaMongo
from datetime import datetime
from bson import ObjectId
import json

app = create_app()
CORS(app)  # Habilitar CORS para todas las rutas

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
        return jsonify(ventas)
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

@app.route('/api/cortes/totales/<int:año>/<int:mes>', methods=['GET'])
def get_totales_mes(año, mes):
    try:
        cortes = CorteCajaMongo(app.db)
        totales = cortes.calcular_totales_del_mes(año, mes)
        return jsonify(totales)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
