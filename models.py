from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "stock": self.stock
        }

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    _products = db.Column('products', db.Text, nullable=False)
    is_invoiced = db.Column(db.Boolean, default=False)
    global_invoice_id = db.Column(db.Integer, db.ForeignKey('global_invoice.id'))
    global_invoice = db.relationship('GlobalInvoice', back_populates='sales')

    @property
    def products(self):
        return json.loads(self._products)

    @products.setter
    def products(self, value):
        self._products = json.dumps(value)

    def to_dict(self):
        return {
            "id": self.id,
            "total_amount": self.total_amount,
            "products": self.products,
            "timestamp": self.timestamp.isoformat(),
            "is_invoiced": self.is_invoiced
        }

class GlobalInvoice(db.Model):
    """Global invoice model"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, nullable=False)
    cfdi_uuid = db.Column(db.String(36), nullable=False)
    folio = db.Column(db.String(10))  # Added folio field
    xml_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sales = db.relationship('Sale', back_populates='global_invoice')

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'total_amount': self.total_amount,
            'tax_amount': self.tax_amount,
            'cfdi_uuid': self.cfdi_uuid,
            'folio': self.folio,
            'xml_content': self.xml_content,
            'created_at': self.created_at.isoformat()
        }

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    cfdi_uuid = db.Column(db.String(36), nullable=False)
    xml_content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sale = db.relationship('Sale', backref=db.backref('invoice', uselist=False))
