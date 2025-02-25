import sqlite3
import os
import sys
from datetime import datetime

def get_sqlite_connection():
    """Get SQLite connection"""
    db_path = os.path.join(os.path.dirname(__file__), 'pos.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def update_all_products_no_track():
    """Update all products to not track stock"""
    try:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        # First check if the track_stock column exists
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'track_stock' not in columns:
            print("La columna track_stock no existe en la tabla de productos.")
            print("Asegúrate de que la aplicación se ha iniciado al menos una vez con la última versión.")
            return False
        
        # Get current count of products
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        print(f"Actualizando {product_count} productos...")
        
        # Update all products to not track stock
        now = datetime.utcnow().isoformat()
        cursor.execute(
            "UPDATE products SET track_stock = 0, updated_at = ?",
            (now,)
        )
        conn.commit()
        
        # Verify the update
        cursor.execute("SELECT COUNT(*) FROM products WHERE track_stock = 0")
        updated_count = cursor.fetchone()[0]
        
        print(f"¡Actualización completada! {updated_count} productos configurados como 'sin contar'.")
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error al actualizar los productos: {str(e)}")
        return False

if __name__ == "__main__":
    print("Actualizando todos los productos para desactivar el seguimiento de stock...")
    success = update_all_products_no_track()
    
    if success:
        print("Operación completada con éxito.")
    else:
        print("La operación no se completó correctamente.")
        sys.exit(1)
