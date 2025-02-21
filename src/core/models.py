from datetime import datetime
from src.core.db import db

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(20))
    sat_key = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sale_details = db.relationship('SaleDetail', backref='product', lazy=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "unit": self.unit,
            "sat_key": self.sat_key,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rfc = db.Column(db.String(13))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sales = db.relationship('Sale', backref='client', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'rfc': self.rfc,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    is_invoiced = db.Column(db.Boolean, default=False)
    invoice_number = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    details = db.relationship('SaleDetail', backref='sale', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'total': self.total,
            'client': self.client.to_dict() if self.client else None,
            'details': [detail.to_dict() for detail in self.details]
        }

class SaleDetail(db.Model):
    __tablename__ = 'sale_details'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product': {
                'id': self.product.id,
                'name': self.product.name,
                'price': self.product.price
            },
            'quantity': self.quantity,
            'price': self.price,
            'subtotal': self.quantity * self.price
        }

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    cfdi_uuid = db.Column(db.String(36), nullable=False)
    xml_content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sale = db.relationship('Sale', backref=db.backref('invoice', uselist=False))

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
