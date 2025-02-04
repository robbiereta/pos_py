from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'stock': self.stock,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_amount = db.Column(db.Float, nullable=False)
    _products = db.Column('products', db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    global_invoice_id = db.Column(db.Integer, db.ForeignKey('global_invoice.id'), nullable=True)
    global_invoice = db.relationship('GlobalInvoice', back_populates='sales')

    @property
    def products(self):
        return json.loads(self._products)

    @products.setter
    def products(self, value):
        self._products = json.dumps(value)

    def to_dict(self):
        return {
            'id': self.id,
            'total_amount': self.total_amount,
            'products': self.products,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'global_invoice_id': self.global_invoice_id
        }

class GlobalInvoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    sales = db.relationship('Sale', back_populates='global_invoice')

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'total_amount': self.total_amount,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'num_sales': len(self.sales)
        }

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    cfdi_uuid = db.Column(db.String(36), nullable=False)
    xml_content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sale = db.relationship('Sale', backref=db.backref('invoice', uselist=False))
