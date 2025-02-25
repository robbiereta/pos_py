from flask_pymongo import PyMongo
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

mongo = PyMongo()
# Create a direct MongoDB client as a fallback
mongo_client = None

def init_db(app):
    """Initialize MongoDB connection"""
    global mongo_client
    mongo.init_app(app, uri=os.getenv('MONGODB_URI'))
    # Also initialize a direct client as a fallback
    mongo_client = MongoClient(os.getenv('MONGODB_URI'))
    return mongo

def get_db():
    """Get MongoDB database instance"""
    try:
        # Try to get database via Flask-PyMongo
        return mongo.db
    except RuntimeError:
        # If we're outside Flask context, use direct client
        global mongo_client
        if mongo_client is None:
            mongo_client = MongoClient(os.getenv('MONGODB_URI'))
        return mongo_client.pos_system
