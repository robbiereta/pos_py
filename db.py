from flask_pymongo import PyMongo
from pymongo import MongoClient
from datetime import datetime
import os

mongo = PyMongo()

def init_db(app):
    """Initialize MongoDB connection"""
    mongo.init_app(app, uri=os.getenv('MONGODB_URI'))
    return mongo

def get_db():
    """Get MongoDB database instance"""
    return mongo.db
