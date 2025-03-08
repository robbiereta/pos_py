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
