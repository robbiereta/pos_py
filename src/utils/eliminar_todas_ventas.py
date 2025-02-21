from flask import Flask
from models import db, Sale, Invoice, GlobalInvoice
from config import config

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    return app

def eliminar_ventas():
    """Elimina todas las ventas y facturas relacionadas"""
    try:
        # Eliminar primero las facturas globales para evitar problemas de FK
        GlobalInvoice.query.delete()
        print("Facturas globales eliminadas")

        # Eliminar facturas individuales
        Invoice.query.delete()
        print("Facturas individuales eliminadas")

        # Eliminar ventas
        Sale.query.delete()
        print("Ventas eliminadas")

        # Guardar los cambios
        db.session.commit()
        print("Todos los registros fueron eliminados exitosamente")

    except Exception as e:
        db.session.rollback()
        print(f"Error al eliminar registros: {str(e)}")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        eliminar_ventas()
