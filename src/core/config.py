import os
from dotenv import load_dotenv
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-12345'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(basedir, "data", "pos.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(basedir, 'data', 'temp')
    
    # Output directories
    OUTPUT_DIR = os.path.join(basedir, 'data', 'output')
    INPUT_DIR = os.path.join(basedir, 'data', 'input')
    
    # Create directories if they don't exist
    for directory in [UPLOAD_FOLDER, OUTPUT_DIR, INPUT_DIR]:
        os.makedirs(directory, exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    CFDI_TEST_MODE = True
    FLASK_ENV = 'development'

class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    CFDI_TEST_MODE = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(basedir, "data", "test.db")}'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    CFDI_TEST_MODE = False
    FLASK_ENV = 'production'
    # Use secure session configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
