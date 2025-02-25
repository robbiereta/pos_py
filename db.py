from flask_pymongo import PyMongo
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
import pymongo

# Load environment variables
load_dotenv()

mongo = PyMongo()
# Create a direct MongoDB client as a fallback
mongo_client = None

def init_db(app):
    """Initialize MongoDB connection"""
    global mongo_client
    try:
        mongo.init_app(app, uri=os.getenv('MONGODB_URI'))
        # Also initialize a direct client as a fallback with shorter timeout
        mongo_client = MongoClient(
            os.getenv('MONGODB_URI'),
            serverSelectionTimeoutMS=5000,  # 5 seconds timeout
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        # Test the connection
        mongo_client.admin.command('ping')
        app.logger.info("MongoDB connection successful")
        return mongo
    except pymongo.errors.ServerSelectionTimeoutError as e:
        app.logger.error(f"MongoDB connection error: {e}")
        # Fallback to local SQLite if MongoDB is not available
        app.logger.warning("Using fallback SQLite database")
        return None
    except Exception as e:
        app.logger.error(f"Unexpected error during MongoDB initialization: {e}")
        return None

def get_db():
    """Get MongoDB database instance"""
    try:
        # Try to get database via Flask-PyMongo
        return mongo.db
    except RuntimeError:
        # If we're outside Flask context, use direct client
        global mongo_client
        if mongo_client is None:
            mongo_client = MongoClient(
                os.getenv('MONGODB_URI'),
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
        try:
            # Test the connection
            mongo_client.admin.command('ping')
            return mongo_client.pos_system
        except Exception as e:
            print(f"MongoDB connection error in get_db: {e}")
            return None
