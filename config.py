import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    MONGO_URI = os.environ.get('MONGODB_URI')
    
    # MongoDB Configuration
    MONGO_DBNAME = 'pos_system'
    MONGO_CONNECT = True
    MONGO_TZ_AWARE = True

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    CFDI_TEST_MODE = True
    FLASK_ENV = 'development'
    MONGO_DBNAME = 'pos_system_dev'

class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    CFDI_TEST_MODE = True
    MONGO_DBNAME = 'pos_system_test'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    CFDI_TEST_MODE = False
    FLASK_ENV = 'production'
    MONGO_DBNAME = 'pos_system_prod'
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
