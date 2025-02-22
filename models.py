from datetime import datetime
from bson import ObjectId

class Category:
    @staticmethod
    def create_category(db, name, description=None):
        category = {
            "name": name,
            "description": description,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = db.categories.insert_one(category)
        category['_id'] = result.inserted_id
        return category

    @staticmethod
    def get_by_id(db, category_id):
        return db.categories.find_one({"_id": ObjectId(category_id)})

    @staticmethod
    def get_by_name(db, name):
        return db.categories.find_one({"name": name})

    @staticmethod
    def update_category(db, category_id, **kwargs):
        kwargs['updated_at'] = datetime.utcnow()
        db.categories.update_one(
            {"_id": ObjectId(category_id)},
            {"$set": kwargs}
        )
        return db.categories.find_one({"_id": ObjectId(category_id)})

class Product:
    @staticmethod
    def create_product(db, name, price, stock=0, description=None, sku=None, image_url=None, min_stock=0, sat_code=None, category_id=None):
        product = {
            "name": name,
            "price": float(price),
            "stock": int(stock),
            "description": description,
            "sku": sku,
            "image_url": image_url,
            "min_stock": int(min_stock),
            "sat_code": sat_code,
            "category_id": ObjectId(category_id) if category_id else None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = db.products.insert_one(product)
        product['_id'] = result.inserted_id
        return product

    @staticmethod
    def get_by_id(db, product_id):
        return db.products.find_one({"_id": ObjectId(product_id)})

    @staticmethod
    def update_product(db, product_id, **kwargs):
        if 'category_id' in kwargs and kwargs['category_id']:
            kwargs['category_id'] = ObjectId(kwargs['category_id'])
        kwargs['updated_at'] = datetime.utcnow()
        db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": kwargs}
        )
        return db.products.find_one({"_id": ObjectId(product_id)})

class Client:
    @staticmethod
    def create_client(db, name, email=None, phone=None, rfc=None, address=None):
        client = {
            "name": name,
            "email": email,
            "phone": phone,
            "rfc": rfc,
            "address": address,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = db.clients.insert_one(client)
        client['_id'] = result.inserted_id
        return client

    @staticmethod
    def get_by_id(db, client_id):
        return db.clients.find_one({"_id": ObjectId(client_id)})

class Sale:
    @staticmethod
    def create_sale(db, client_id, total_amount, amount_received, change_amount, details, date=None):
        sale = {
            "client_id": ObjectId(client_id),
            "date": date if date else datetime.utcnow(),
            "total_amount": float(total_amount),
            "amount_received": float(amount_received),
            "change_amount": float(change_amount),
            "is_invoiced": False,
            "invoice_uuid": None,
            "invoice_date": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "details": details,
            "global_invoice_id": None
        }
        result = db.sales.insert_one(sale)
        sale['_id'] = result.inserted_id
        return sale

    @staticmethod
    def get_by_id(db, sale_id):
        return db.sales.find_one({"_id": ObjectId(sale_id)})

    @staticmethod
    def update_sale(db, sale_id, **kwargs):
        kwargs['updated_at'] = datetime.utcnow()
        db.sales.update_one(
            {"_id": ObjectId(sale_id)},
            {"$set": kwargs}
        )
        return db.sales.find_one({"_id": ObjectId(sale_id)})

    @staticmethod
    def get_uninvoiced_sales(db):
        """Get all sales that haven't been invoiced"""
        return list(db.sales.find({"is_invoiced": False}))

class SaleDetail:
    @staticmethod
    def create_sale_detail(db, sale_id, product_id, quantity, price):
        sale_detail = {
            "sale_id": ObjectId(sale_id),
            "product_id": ObjectId(product_id),
            "quantity": int(quantity),
            "price": float(price),
            "created_at": datetime.utcnow()
        }
        result = db.sale_details.insert_one(sale_detail)
        sale_detail['_id'] = result.inserted_id
        return sale_detail

    @staticmethod
    def get_by_id(db, sale_detail_id):
        return db.sale_details.find_one({"_id": ObjectId(sale_detail_id)})

class Invoice:
    @staticmethod
    def create_invoice(db, sale_id, cfdi_uuid, xml_content, timestamp):
        invoice = {
            "sale_id": ObjectId(sale_id),
            "cfdi_uuid": cfdi_uuid,
            "xml_content": xml_content,
            "timestamp": timestamp
        }
        result = db.invoices.insert_one(invoice)
        invoice['_id'] = result.inserted_id
        return invoice

    @staticmethod
    def get_by_id(db, invoice_id):
        return db.invoices.find_one({"_id": ObjectId(invoice_id)})

class GlobalInvoice:
    @staticmethod
    def create_global_invoice(db, date, total_amount, tax_amount, cfdi_uuid, folio, xml_content, sale_ids):
        global_invoice = {
            "date": date,
            "total_amount": float(total_amount),
            "tax_amount": float(tax_amount),
            "cfdi_uuid": cfdi_uuid,
            "folio": folio,
            "xml_content": xml_content,
            "created_at": datetime.utcnow(),
            "sale_ids": [ObjectId(sale_id) for sale_id in sale_ids]
        }
        result = db.global_invoices.insert_one(global_invoice)
        global_invoice['_id'] = result.inserted_id

        # Update all related sales
        db.sales.update_many(
            {"_id": {"$in": global_invoice["sale_ids"]}},
            {"$set": {
                "global_invoice_id": result.inserted_id,
                "is_invoiced": True
            }}
        )
        return global_invoice

    @staticmethod
    def get_by_id(db, invoice_id):
        return db.global_invoices.find_one({"_id": ObjectId(invoice_id)})
