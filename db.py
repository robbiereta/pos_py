from flask_pymongo import PyMongo
from pymongo import MongoClient
from datetime import datetime

mongo = PyMongo()

def init_db(app):
    """Initialize MongoDB connection"""
    mongo.init_app(app)
    return mongo

def get_db():
    """Get MongoDB database instance"""
    return mongo.db
