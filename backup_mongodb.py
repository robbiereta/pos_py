import os
import sqlite3
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_mongo_connection():
    """Get MongoDB connection"""
    try:
        mongo_uri = os.getenv('MONGODB_URI')
        if not mongo_uri:
            logger.error("MongoDB URI not found in environment variables")
            return None
            
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=30000,  # 30 seconds timeout
            connectTimeoutMS=30000
        )
        
        # Test the connection
        client.admin.command('ping')
        logger.info("MongoDB connection successful")
        return client
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        return None

def get_sqlite_connection():
    """Get SQLite connection"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'pos.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        logger.info(f"SQLite database connected at: {db_path}")
        return conn
    except Exception as e:
        logger.error(f"SQLite connection error: {e}")
        return None

def setup_sqlite_tables(conn):
    """Set up SQLite tables"""
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        price REAL DEFAULT 0,
        stock INTEGER DEFAULT 0,
        description TEXT,
        sku TEXT,
        image_url TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    ''')
    
    # Create clients table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        rfc TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        created_at TEXT,
        updated_at TEXT,
        mongo_id TEXT
    )
    ''')
    
    # Create sales table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        total REAL DEFAULT 0,
        items TEXT,  -- JSON string of items
        date TEXT,
        invoice_status TEXT,
        notes TEXT,
        created_at TEXT,
        updated_at TEXT,
        mongo_id TEXT,
        FOREIGN KEY (client_id) REFERENCES clients (id)
    )
    ''')
    
    conn.commit()
    logger.info("SQLite tables created successfully")

def backup_collection(mongo_db, sqlite_conn, collection_name, table_name):
    """Backup a MongoDB collection to SQLite table"""
    try:
        cursor = sqlite_conn.cursor()
        
        # Get collection data
        mongo_data = list(mongo_db[collection_name].find())
        if not mongo_data:
            logger.warning(f"No data found in MongoDB collection: {collection_name}")
            return 0
            
        count = 0
        
        if table_name == 'products':
            # Clear existing data
            cursor.execute("DELETE FROM products")
            sqlite_conn.commit()
            
            # Insert products
            for product in mongo_data:
                try:
                    cursor.execute('''
                    INSERT INTO products (name, price, stock, description, sku, image_url, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        product.get('name', ''),
                        float(product.get('price', 0)),
                        int(product.get('stock', 0)),
                        product.get('description', ''),
                        product.get('sku', ''),
                        product.get('image_url', ''),
                        product.get('created_at', datetime.utcnow()).isoformat() if isinstance(product.get('created_at'), datetime) else str(product.get('created_at', '')),
                        product.get('updated_at', datetime.utcnow()).isoformat() if isinstance(product.get('updated_at'), datetime) else str(product.get('updated_at', ''))
                    ))
                    count += 1
                    logger.info(f"Product backed up: {product.get('name')}")
                except sqlite3.IntegrityError:
                    logger.warning(f"Duplicate product name: {product.get('name')}")
                except Exception as e:
                    logger.error(f"Error inserting product {product.get('name')}: {e}")
        
        elif table_name == 'clients':
            # Clear existing data
            cursor.execute("DELETE FROM clients")
            sqlite_conn.commit()
            
            # Insert clients
            for client in mongo_data:
                try:
                    cursor.execute('''
                    INSERT INTO clients (name, rfc, email, phone, address, created_at, updated_at, mongo_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        client.get('name', ''),
                        client.get('rfc', ''),
                        client.get('email', ''),
                        client.get('phone', ''),
                        client.get('address', ''),
                        client.get('created_at', datetime.utcnow()).isoformat() if isinstance(client.get('created_at'), datetime) else str(client.get('created_at', '')),
                        client.get('updated_at', datetime.utcnow()).isoformat() if isinstance(client.get('updated_at'), datetime) else str(client.get('updated_at', '')),
                        str(client.get('_id', ''))
                    ))
                    count += 1
                except Exception as e:
                    logger.error(f"Error inserting client {client.get('name')}: {e}")
        
        elif table_name == 'sales':
            # Clear existing data
            cursor.execute("DELETE FROM sales")
            sqlite_conn.commit()
            
            # Insert sales
            for sale in mongo_data:
                try:
                    # Convert items to JSON string
                    items_json = json.dumps(sale.get('items', []))
                    
                    # Get client_id from mongo_id
                    client_id = None
                    if 'client' in sale and '_id' in sale['client']:
                        client_mongo_id = str(sale['client']['_id'])
                        cursor.execute("SELECT id FROM clients WHERE mongo_id = ?", (client_mongo_id,))
                        result = cursor.fetchone()
                        if result:
                            client_id = result['id']
                    
                    cursor.execute('''
                    INSERT INTO sales (client_id, total, items, date, invoice_status, notes, created_at, updated_at, mongo_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        client_id,
                        float(sale.get('total', 0)),
                        items_json,
                        sale.get('date', datetime.utcnow().date().isoformat()) if isinstance(sale.get('date'), datetime) else str(sale.get('date', '')),
                        sale.get('invoice_status', ''),
                        sale.get('notes', ''),
                        sale.get('created_at', datetime.utcnow()).isoformat() if isinstance(sale.get('created_at'), datetime) else str(sale.get('created_at', '')),
                        sale.get('updated_at', datetime.utcnow()).isoformat() if isinstance(sale.get('updated_at'), datetime) else str(sale.get('updated_at', '')),
                        str(sale.get('_id', ''))
                    ))
                    count += 1
                except Exception as e:
                    logger.error(f"Error inserting sale: {e}")
        
        sqlite_conn.commit()
        logger.info(f"Backed up {count} records from {collection_name} to {table_name}")
        return count
    except Exception as e:
        logger.error(f"Error backing up collection {collection_name}: {e}")
        return 0

def main():
    """Main backup function"""
    # Connect to MongoDB
    mongo_client = get_mongo_connection()
    if not mongo_client:
        logger.error("Failed to connect to MongoDB, backup aborted")
        return
    
    # Connect to SQLite
    sqlite_conn = get_sqlite_connection()
    if not sqlite_conn:
        logger.error("Failed to connect to SQLite, backup aborted")
        return
    
    # Setup SQLite tables
    setup_sqlite_tables(sqlite_conn)
    
    # Get MongoDB database
    mongo_db = mongo_client.get_database('pos_system')
    
    # Backup collections
    total_records = 0
    total_records += backup_collection(mongo_db, sqlite_conn, 'products', 'products')
    total_records += backup_collection(mongo_db, sqlite_conn, 'clients', 'clients')
    total_records += backup_collection(mongo_db, sqlite_conn, 'sales', 'sales')
    
    # Close connections
    sqlite_conn.close()
    mongo_client.close()
    
    logger.info(f"Backup completed successfully. Total records: {total_records}")
    print(f"MongoDB backup completed successfully. Total records: {total_records}")

if __name__ == '__main__':
    main()
