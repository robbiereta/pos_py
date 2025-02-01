from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from models import db, Sale, Invoice, GlobalInvoice, Product
from datetime import datetime
from cfdi_generator import cfdi_generator, cfdi_generator_prod
from config import config
import os
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables
load_dotenv()

def create_app(config_name='default'):
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    app.config.from_object(config[config_name])
    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/health')
    def health_check():
        """Health check endpoint for fly.io"""
        try:
            # Test database connection
            db.session.execute(text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': db_status
        })

    @app.route('/products', methods=['GET'])
    def get_products():
        """Get all products"""
        products = Product.query.all()
        return jsonify([product.to_dict() for product in products])

    @app.route('/products', methods=['POST'])
    def add_product():
        """Add a new product"""
        data = request.get_json()
        
        if not data or 'name' not in data or 'price' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
            
        product = Product(
            name=data['name'],
            price=data['price'],
            stock=data.get('stock', 0)
        )
        
        try:
            db.session.add(product)
            db.session.commit()
            return jsonify(product.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/sales', methods=['POST'])
    def create_sale():
        """Create a new sale"""
        data = request.get_json()
        
        if not data or 'total_amount' not in data or 'products' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
            
        sale = Sale(
            total_amount=data['total_amount'],
            products=data['products']
        )
        
        try:
            db.session.add(sale)
            db.session.commit()
            
            # Generate invoice if requested
            if data.get('generate_invoice'):
                try:
                    generator = cfdi_generator if app.config['CFDI_TEST_MODE'] else cfdi_generator_prod
                    invoice_data = generator.generate_cfdi(sale)
                    return jsonify({
                        'sale_id': sale.id,
                        'cfdi_invoice': invoice_data
                    })
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            return jsonify({
                'message': 'Sale created successfully',
                'id': sale.id,
                'total_amount': sale.total_amount,
                'products': sale.products
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/sales/pending', methods=['GET'])
    def get_pending_sales():
        """Get all pending sales"""
        try:
            sales = Sale.query.filter_by(is_invoiced=False).all()
            return jsonify([{
                'id': sale.id,
                'total_amount': sale.total_amount,
                'products': sale.products,
                'timestamp': sale.timestamp.isoformat()
            } for sale in sales])
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/global-invoice', methods=['POST'])
    def generate_global_invoice():
        """Generate a global invoice"""
        data = request.get_json()
        date = datetime.strptime(data['date'], '%Y-%m-%d').date() if data and 'date' in data else datetime.utcnow().date()
        
        # Get all uninvoiced sales
        sales = Sale.query.filter_by(is_invoiced=False).all()
        if not sales:
            return jsonify({'error': 'No pending sales found'}), 404
        
        try:
            generator = cfdi_generator if app.config['CFDI_TEST_MODE'] else cfdi_generator_prod
            result = generator.generate_global_cfdi(sales, date)
            
            # Create global invoice record
            global_invoice = GlobalInvoice(
                date=date,
                total_amount=sum(sale.total_amount for sale in sales),
                tax_amount=sum(sale.total_amount * 0.16 for sale in sales),
                cfdi_uuid=result.get('uuid', ''),
                xml_content=result.get('xml', '')
            )
            
            # Mark all sales as invoiced
            for sale in sales:
                sale.is_invoiced = True
                sale.global_invoice = global_invoice
            
            db.session.add(global_invoice)
            db.session.commit()
            
            return jsonify(global_invoice.to_dict())
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/global-invoice/history', methods=['GET'])
    def get_global_invoices():
        """Get history of global invoices"""
        try:
            global_invoices = GlobalInvoice.query.order_by(GlobalInvoice.date.desc()).all()
            return jsonify([invoice.to_dict() for invoice in global_invoices])
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'default'))
    app.run(debug=True)
