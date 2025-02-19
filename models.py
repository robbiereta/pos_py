from datetime import datetime
from db import db

class Product(db.Model):
    __tablename__ = 'products'
    
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

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    rfc = db.Column(db.String(13))  # RFC para facturación
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with sales
    sales = db.relationship('Sale', back_populates='client', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'rfc': self.rfc,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    amount_received = db.Column(db.Float, nullable=False)
    change_amount = db.Column(db.Float, nullable=False)
    is_invoiced = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    global_invoice_id = db.Column(db.Integer, db.ForeignKey('global_invoice.id'), nullable=True)
    
    # Relationships
    details = db.relationship('SaleDetail', back_populates='sale', lazy=True)
    global_invoice = db.relationship('GlobalInvoice', back_populates='sales')
    client = db.relationship('Client', back_populates='sales', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'total_amount': self.total_amount,
            'amount_received': self.amount_received,
            'change_amount': self.change_amount,
            'is_invoiced': self.is_invoiced,
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
    
    # Relationships
    sale = db.relationship('Sale', back_populates='details')
    product = db.relationship('Product')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
