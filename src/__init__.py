from flask import Flask
from src.core.config import Config
from src.core.db import init_db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize database
    init_db(app)

    # Register blueprints
    from src.routes.pos import pos_bp
    from src.routes.clients import clients_bp
    from src.routes.invoice_ocr import invoice_ocr_bp
    from src.routes.export import export_bp

    app.register_blueprint(pos_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(invoice_ocr_bp)
    app.register_blueprint(export_bp)

    return app
