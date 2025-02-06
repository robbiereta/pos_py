from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    sku = db.Column(db.String(50), unique=True)
    image_url = db.Column(db.String(255))
    min_stock = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "description": self.description,
            "sku": self.sku,
            "image_url": self.image_url,
            "min_stock": self.min_stock,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    amount_received = db.Column(db.Float, nullable=False)
    change_amount = db.Column(db.Float, nullable=False)
    is_invoiced = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    global_invoice_id = db.Column(db.Integer, db.ForeignKey('global_invoice.id'), nullable=True)
    global_invoice = db.relationship('GlobalInvoice', back_populates='sales')

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "total_amount": self.total_amount,
            "amount_received": self.amount_received,
            "change_amount": self.change_amount,
            "is_invoiced": self.is_invoiced,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class SaleDetail(db.Model):
    __tablename__ = 'sale_details'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    # Relaciones
    sale = db.relationship('Sale', backref=db.backref('details', lazy=True))
    product = db.relationship('Product')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GlobalInvoice(db.Model):
    """Global invoice model"""
    __tablename__ = 'global_invoice'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, nullable=False)
    cfdi_uuid = db.Column(db.String(36), nullable=False)
    folio = db.Column(db.String(10))
    xml_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sales = db.relationship('Sale', back_populates='global_invoice', lazy='dynamic')

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "total_amount": self.total_amount,
            "tax_amount": self.tax_amount,
            "cfdi_uuid": self.cfdi_uuid,
            "folio": self.folio,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    cfdi_uuid = db.Column(db.String(36), nullable=False)
    xml_content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sale = db.relationship('Sale', backref=db.backref('invoice', uselist=False))
