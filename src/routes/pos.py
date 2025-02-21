from flask import Blueprint, render_template, request, jsonify
from src.core.models import Product, Sale, SaleDetail, Client
from src.core.db import db

pos_bp = Blueprint('pos', __name__)

@pos_bp.route('/')
def index():
    return render_template('index.html')

@pos_bp.route('/api/productos', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'price': p.price,
        'stock': p.stock,
        'image_url': p.image_url
    } for p in products])

@pos_bp.route('/api/sales', methods=['POST'])
def create_sale():
    data = request.json
    try:
        # Create sale
        sale = Sale(
            total_amount=data['total_amount'],
            amount_received=data['amount_received'],
            change_amount=data['change_amount'],
            client_id=data.get('client_id'),
            is_invoiced=data.get('is_invoiced', False)
        )
        db.session.add(sale)
        db.session.flush()  # Get sale ID without committing

        # Create sale details
        for detail in data['details']:
            sale_detail = SaleDetail(
                sale_id=sale.id,
                product_id=detail['product_id'],
                quantity=detail['quantity'],
                price=detail['price']
            )
            db.session.add(sale_detail)

            # Update product stock
            product = Product.query.get(detail['product_id'])
            if product:
                product.stock -= detail['quantity']

        db.session.commit()
        return jsonify({'id': sale.id, 'message': 'Venta creada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@pos_bp.route('/sales', methods=['GET'])
def get_sales():
    try:
        sales = Sale.query.order_by(Sale.date.desc()).all()
        return jsonify({
            'sales': [{
                'id': s.id,
                'date': s.date.isoformat(),
                'total_amount': s.total_amount,
                'is_invoiced': s.is_invoiced,
                'client': s.client.name if s.client else None
            } for s in sales]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@pos_bp.route('/sales/<int:sale_id>', methods=['GET'])
def get_sale(sale_id):
    try:
        sale = Sale.query.get_or_404(sale_id)
        return jsonify({
            'id': sale.id,
            'date': sale.date.isoformat(),
            'total_amount': sale.total_amount,
            'amount_received': sale.amount_received,
            'change_amount': sale.change_amount,
            'is_invoiced': sale.is_invoiced,
            'client': sale.client.name if sale.client else None,
            'products': [{
                'id': detail.product.id,
                'name': detail.product.name,
                'quantity': detail.quantity,
                'price': detail.price
            } for detail in sale.details]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
