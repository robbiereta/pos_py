from flask import Flask, request, jsonify, render_template, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from models import db, Sale, Invoice, GlobalInvoice, Product
from datetime import datetime
from cfdi_generator import cfdi_generator, cfdi_generator_prod
from config import config
import os
from dotenv import load_dotenv
from sqlalchemy import text
import pandas as pd
from werkzeug.utils import secure_filename
import requests

# Load environment variables
load_dotenv()

def create_app(config_name='default'):
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    app.config.from_object(config[config_name])
    db.init_app(app)
    migrate = Migrate(app, db)

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

    @app.route('/sales', methods=['GET'])
    def get_sales():
        """Get all sales with optional filters"""
        try:
            # Get query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            min_amount = request.args.get('min_amount', type=float)
            max_amount = request.args.get('max_amount', type=float)
            
            # Base query
            query = Sale.query
            
            # Apply filters
            if start_date:
                query = query.filter(Sale.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
            if end_date:
                query = query.filter(Sale.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))
            if min_amount is not None:
                query = query.filter(Sale.total_amount >= min_amount)
            if max_amount is not None:
                query = query.filter(Sale.total_amount <= max_amount)
            
            # Order by timestamp descending
            query = query.order_by(Sale.timestamp.desc())
            
            # Paginate results
            pagination = query.paginate(page=page, per_page=per_page)
            
            return jsonify({
                'sales': [{
                    'id': sale.id,
                    'timestamp': sale.timestamp.isoformat(),
                    'total_amount': sale.total_amount,
                    'products': sale.products,
                    'is_invoiced': sale.is_invoiced
                } for sale in pagination.items],
                'total_pages': pagination.pages,
                'current_page': page,
                'total_items': pagination.total
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/sales/<int:sale_id>', methods=['GET'])
    def get_sale(sale_id):
        """Get a specific sale by ID"""
        try:
            sale = Sale.query.get_or_404(sale_id)
            return jsonify({
                'id': sale.id,
                'timestamp': sale.timestamp.isoformat(),
                'total_amount': sale.total_amount,
                'products': sale.products,
                'is_invoiced': sale.is_invoiced
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/sales/<int:sale_id>', methods=['PUT'])
    def update_sale(sale_id):
        """Update a specific sale"""
        try:
            sale = Sale.query.get_or_404(sale_id)
            
            # Don't allow updating invoiced sales
            if sale.is_invoiced:
                return jsonify({'error': 'Cannot update an invoiced sale'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Update fields
            if 'total_amount' in data:
                sale.total_amount = data['total_amount']
            if 'products' in data:
                sale.products = data['products']
            
            db.session.commit()
            
            return jsonify({
                'message': 'Sale updated successfully',
                'id': sale.id,
                'timestamp': sale.timestamp.isoformat(),
                'total_amount': sale.total_amount,
                'products': sale.products,
                'is_invoiced': sale.is_invoiced
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/sales/<int:sale_id>', methods=['DELETE'])
    def delete_sale(sale_id):
        """Delete a specific sale"""
        try:
            sale = Sale.query.get_or_404(sale_id)
            
            # Don't allow deleting invoiced sales
            if sale.is_invoiced:
                return jsonify({'error': 'Cannot delete an invoiced sale'}), 400
            
            db.session.delete(sale)
            db.session.commit()
            
            return jsonify({
                'message': 'Sale deleted successfully',
                'id': sale_id
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/sales/stats', methods=['GET'])
    def get_sales_stats():
        """Get sales statistics"""
        try:
            # Get query parameters
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Base query
            query = Sale.query
            
            # Apply date filters
            if start_date:
                query = query.filter(Sale.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
            if end_date:
                query = query.filter(Sale.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))
            
            # Calculate statistics
            sales = query.all()
            total_sales = len(sales)
            total_amount = sum(sale.total_amount for sale in sales)
            avg_amount = total_amount / total_sales if total_sales > 0 else 0
            min_amount = min((sale.total_amount for sale in sales), default=0)
            max_amount = max((sale.total_amount for sale in sales), default=0)
            
            return jsonify({
                'total_sales': total_sales,
                'total_amount': total_amount,
                'average_amount': avg_amount,
                'min_amount': min_amount,
                'max_amount': max_amount,
                'period_start': start_date,
                'period_end': end_date
            })
            
        except Exception as e:
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
            # Always use production generator for global invoices
            result = cfdi_generator_prod.generate_global_cfdi(sales, date)
            
            # Calculate totals
            total_amount = sum(sale.total_amount for sale in sales)
            subtotal = total_amount / 1.16  # VAT is included in total
            tax_amount = total_amount - subtotal
            
            # Create global invoice record
            global_invoice = GlobalInvoice(
                date=date,
                total_amount=total_amount,
                tax_amount=tax_amount,
                cfdi_uuid=result.get('uuid', ''),
                folio=result.get('folio', None),
                xml_content=result.get('xml', '')
            )
            
            # Save global invoice
            db.session.add(global_invoice)
            
            # Mark sales as invoiced and associate them with the global invoice
            for sale in sales:
                sale.is_invoiced = True
                sale.global_invoice = global_invoice
            
            # Save changes
            db.session.commit()
            
            return jsonify({
                'id': global_invoice.id,
                'date': global_invoice.date.strftime('%Y-%m-%d'),
                'total_amount': global_invoice.total_amount,
                'tax_amount': global_invoice.tax_amount,
                'cfdi_uuid': global_invoice.cfdi_uuid,
                'folio': global_invoice.folio,
                'xml_content': global_invoice.xml_content,
                'created_at': global_invoice.created_at.isoformat()
            })
            
        except Exception as e:
            return jsonify({'error': f'Error generating Global CFDI: {str(e)}'}), 500

    @app.route('/api/global_invoices', methods=['GET'])
    def get_global_invoices():
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            query = GlobalInvoice.query
            
            if start_date:
                query = query.filter(GlobalInvoice.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
            if end_date:
                query = query.filter(GlobalInvoice.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
            
            invoices = query.order_by(GlobalInvoice.date.desc()).all()
            return jsonify([{
                'date': invoice.date.strftime('%Y-%m-%d'),
                'folio': invoice.folio,
                'cfdi_uuid': invoice.cfdi_uuid,
                'total_amount': invoice.total_amount
            } for invoice in invoices])
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/global-invoice/history', methods=['GET'])
    def get_global_invoices_history():
        """Get history of global invoices"""
        try:
            global_invoices = GlobalInvoice.query.order_by(GlobalInvoice.date.desc()).all()
            return jsonify([{
                'date': invoice.date.strftime('%Y-%m-%d'),
                'folio': invoice.folio,
                'cfdi_uuid': invoice.cfdi_uuid,
                'total_amount': invoice.total_amount
            } for invoice in global_invoices])
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/global_invoices/<uuid>/xml', methods=['GET'])
    def download_global_invoice_xml(uuid):
        try:
            invoice = GlobalInvoice.query.filter_by(cfdi_uuid=uuid).first()
            if not invoice:
                return jsonify({'error': 'Factura no encontrada'}), 404
                
            response = make_response(invoice.xml_content)
            response.headers['Content-Type'] = 'application/xml'
            response.headers['Content-Disposition'] = f'attachment; filename=factura_global_{invoice.date.strftime("%Y%m%d")}_{uuid}.xml'
            return response
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/download_global_xml/<uuid>')
    def download_global_xml(uuid):
        """Download XML for a global invoice"""
        try:
            # Get XML content from database
            invoice = db.session.query(GlobalInvoice).filter_by(cfdi_uuid=uuid).first()
            if not invoice:
                return "Factura no encontrada", 404
                
            # Create XML response
            response = make_response(invoice.xml_content)
            response.headers['Content-Type'] = 'application/xml'
            response.headers['Content-Disposition'] = f'attachment; filename=factura_global_{uuid}.xml'
            return response
        except Exception as e:
            return str(e), 500

    @app.route('/download_global_pdf/<uuid>')
    def download_global_pdf(uuid):
        """Download PDF for a global invoice"""
        try:
            # Get invoice data
            invoice = db.session.query(GlobalInvoice).filter_by(cfdi_uuid=uuid).first()
            if not invoice:
                return "Factura no encontrada", 404
                
            # Get PDF from SW Sapien API using the UUID
            url = f"{os.getenv('SW_URL')}/pdf/v1/cfdi"
            headers = {
                'Authorization': f"Bearer {os.getenv('SW_TOKEN')}",
                'Content-Type': 'application/json'
            }
            data = {
                'uuid': uuid,
                'type': 'issued'
            }
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                # Create PDF response
                pdf_response = make_response(response.content)
                pdf_response.headers['Content-Type'] = 'application/pdf'
                pdf_response.headers['Content-Disposition'] = f'attachment; filename=factura_global_{uuid}.pdf'
                return pdf_response
            else:
                return f"Error al obtener PDF: {response.text}", 500
        except Exception as e:
            return str(e), 500

    @app.route('/download_global_xml_from_pac/<uuid>')
    def download_global_xml_from_pac(uuid):
        """Download XML directly from PAC for a global invoice"""
        try:
            # Get invoice to verify it exists
            invoice = db.session.query(GlobalInvoice).filter_by(cfdi_uuid=uuid).first()
            if not invoice:
                return "Factura no encontrada", 404

            # Download XML from PAC
            xml_content = cfdi_generator_prod.download_xml_from_pac(uuid)
                
            # Create XML response
            response = make_response(xml_content)
            response.headers['Content-Type'] = 'application/xml'
            response.headers['Content-Disposition'] = f'attachment; filename=factura_global_pac_{uuid}.xml'
            return response
        except Exception as e:
            return str(e), 500

    @app.route('/upload-sales', methods=['POST'])
    def upload_sales():
        """Import sales from Excel file"""
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not file.filename.endswith('.xlsx'):
            return jsonify({'error': 'File must be an Excel (.xlsx) file'}), 400
            
        try:
            # Read Excel file
            df = pd.read_excel(file)
            
            # Validate required columns
            required_columns = ['products', 'total_amount']
            if not all(col in df.columns for col in required_columns):
                return jsonify({'error': 'Excel file must contain columns: ' + ', '.join(required_columns)}), 400
            
            # Process each row
            sales_created = []
            for _, row in df.iterrows():
                # Create sale object
                sale = Sale(
                    total_amount=float(row['total_amount']),
                    products=row['products']
                )
                
                db.session.add(sale)
                sales_created.append({
                    'total_amount': sale.total_amount,
                    'products': sale.products
                })
            
            db.session.commit()
            
            return jsonify({
                'message': f'Successfully imported {len(sales_created)} sales',
                'sales': sales_created
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/upload-products', methods=['POST'])
    def upload_products():
        """Import products from Excel file"""
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not file.filename.endswith('.xlsx'):
            return jsonify({'error': 'File must be an Excel (.xlsx) file'}), 400
            
        try:
            # Read Excel file
            df = pd.read_excel(file)
            
            # Validate required columns
            required_columns = ['name', 'price']
            if not all(col in df.columns for col in required_columns):
                return jsonify({'error': 'Excel file must contain columns: ' + ', '.join(required_columns)}), 400
            
            # Process each row
            products_created = []
            for _, row in df.iterrows():
                # Check if product already exists
                existing_product = Product.query.filter_by(name=row['name']).first()
                if existing_product:
                    # Update existing product
                    existing_product.price = float(row['price'])
                    existing_product.stock = int(row.get('stock', 0))
                    products_created.append({
                        'name': existing_product.name,
                        'price': existing_product.price,
                        'stock': existing_product.stock,
                        'status': 'updated'
                    })
                else:
                    # Create new product
                    product = Product(
                        name=row['name'],
                        price=float(row['price']),
                        stock=int(row.get('stock', 0))
                    )
                    db.session.add(product)
                    products_created.append({
                        'name': product.name,
                        'price': product.price,
                        'stock': product.stock,
                        'status': 'created'
                    })
            
            db.session.commit()
            
            return jsonify({
                'message': f'Successfully processed {len(products_created)} products',
                'products': products_created
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'default'))
    app.run(debug=True)
