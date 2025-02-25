import os
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

def check_table_structure(conn):
    """Check if the SQLite tables have the correct structure and update if needed"""
    cursor = conn.cursor()
    
    # Check products table structure
    cursor.execute("PRAGMA table_info(products)")
    columns = {col[1]: col for col in cursor.fetchall()}
    
    # Add missing columns if needed
    if 'description' not in columns:
        logger.info("Adding 'description' column to products table")
        cursor.execute("ALTER TABLE products ADD COLUMN description TEXT")
    
    if 'stock' not in columns:
        logger.info("Adding 'stock' column to products table")
        cursor.execute("ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 0")
    
    if 'image_url' not in columns:
        logger.info("Adding 'image_url' column to products table")
        cursor.execute("ALTER TABLE products ADD COLUMN image_url TEXT")
    
    conn.commit()
    logger.info("Product table structure checked and updated if needed")
    
    # You can add similar checks for other tables as needed

def vacuum_database(conn):
    """Vacuum the database to reclaim space"""
    try:
        conn.execute("VACUUM")
        logger.info("Database vacuumed successfully")
    except Exception as e:
        logger.error(f"Error vacuuming database: {e}")

def analyze_database(conn):
    """Analyze the database to optimize queries"""
    try:
        conn.execute("ANALYZE")
        logger.info("Database analyzed successfully")
    except Exception as e:
        logger.error(f"Error analyzing database: {e}")

def main():
    """Main maintenance function"""
    print("Starting database maintenance...")
    
    conn = get_sqlite_connection()
    if not conn:
        print("Failed to connect to the database. Maintenance aborted.")
        return
    
    try:
        # Check and update table structure
        check_table_structure(conn)
        
        # Vacuum database to reclaim space
        vacuum_database(conn)
        
        # Analyze database for query optimization
        analyze_database(conn)
        
        print("Database maintenance completed successfully.")
    except Exception as e:
        logger.error(f"Error during maintenance: {e}")
        print(f"Error during maintenance: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
