from convertir_ventas import create_app
import sqlite3
from datetime import datetime

def migrar_cortes_a_mongo():
    """
    Migra los cortes de caja de SQLite a MongoDB
    """
    app = create_app()
    
    with app.app_context():
        try:
            # Conectar a SQLite
            sqlite_conn = sqlite3.connect('pos.db')
            cursor = sqlite_conn.cursor()
            
            # Crear tabla si no existe
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cortes_caja (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    monto_inicial DECIMAL(10,2) DEFAULT 0,
                    monto_final DECIMAL(10,2) DEFAULT 0,
                    ventas_efectivo DECIMAL(10,2) DEFAULT 0,
                    ventas_tarjeta DECIMAL(10,2) DEFAULT 0,
                    ventas_transferencia DECIMAL(10,2) DEFAULT 0,
                    retiros DECIMAL(10,2) DEFAULT 0,
                    notas TEXT
                )
            ''')
            sqlite_conn.commit()
            
            # Insertar un corte de ejemplo si no hay ninguno
            cursor.execute('SELECT COUNT(*) FROM cortes_caja')
            if cursor.fetchone()[0] == 0:
                print("\nCreando corte de ejemplo...")
                cursor.execute('''
                    INSERT INTO cortes_caja (
                        fecha_hora, monto_inicial, monto_final, 
                        ventas_efectivo, ventas_tarjeta, ventas_transferencia,
                        retiros, notas
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    '2025-03-08 13:19:37.654710',
                    1000.00,
                    14789.00,
                    14789.00,
                    0.00,
                    0.00,
                    0.00,
                    'Corte de ejemplo'
                ))
                sqlite_conn.commit()
            
            # Obtener los cortes de SQLite
            cursor.execute('''
                SELECT id, fecha_hora, monto_inicial, monto_final, 
                       ventas_efectivo, ventas_tarjeta, ventas_transferencia,
                       retiros, notas
                FROM cortes_caja
            ''')
            cortes = cursor.fetchall()
            
            print(f"\nMigrando {len(cortes)} cortes de caja...")
            
            # Obtener colección de MongoDB
            db = app.db
            cortes_mongo = db.cortes_caja
            
            # Migrar cada corte
            for corte in cortes:
                corte_dict = {
                    'sqlite_id': corte[0],
                    'fecha_hora': datetime.strptime(corte[1], '%Y-%m-%d %H:%M:%S.%f'),
                    'monto_inicial': float(corte[2]),
                    'monto_final': float(corte[3]),
                    'ventas_efectivo': float(corte[4]),
                    'ventas_tarjeta': float(corte[5]),
                    'ventas_transferencia': float(corte[6]),
                    'retiros': float(corte[7]),
                    'notas': corte[8]
                }
                
                # Verificar si ya existe
                existing = cortes_mongo.find_one({'sqlite_id': corte[0]})
                if not existing:
                    cortes_mongo.insert_one(corte_dict)
                    print(f"Migrado corte {corte[0]} del {corte[1]}")
                else:
                    print(f"El corte {corte[0]} ya existe en MongoDB")
            
            print("\n¡Migración completada!")
            
            # Cerrar conexión SQLite
            sqlite_conn.close()
            
        except Exception as e:
            print(f"Error durante la migración: {str(e)}")

if __name__ == "__main__":
    migrar_cortes_a_mongo()
