import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class CorteCaja:
    def __init__(self, db_path: str = "pos_database.db"):
        self.db_path = db_path
        self.create_table()
    
    def create_table(self):
        """Create the cortes_caja table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cortes_caja (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_hora DATETIME NOT NULL,
                efectivo_inicial REAL NOT NULL,
                efectivo_final REAL NOT NULL,
                ventas_efectivo REAL NOT NULL,
                ventas_tarjeta REAL NOT NULL,
                ventas_transferencia REAL NOT NULL,
                retiros REAL NOT NULL,
                notas TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def crear_corte(self, efectivo_inicial: float, efectivo_final: float,
                    ventas_efectivo: float, ventas_tarjeta: float,
                    ventas_transferencia: float, retiros: float,
                    notas: str = "") -> int:
        """
        Crear un nuevo corte de caja
        Retorna el ID del nuevo corte creado
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO cortes_caja (
                fecha_hora, efectivo_inicial, efectivo_final,
                ventas_efectivo, ventas_tarjeta, ventas_transferencia,
                retiros, notas
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now(), efectivo_inicial, efectivo_final,
              ventas_efectivo, ventas_tarjeta, ventas_transferencia,
              retiros, notas))
        
        nuevo_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return nuevo_id

    def obtener_corte(self, corte_id: int) -> Optional[Dict]:
        """
        Obtener un corte de caja por su ID
        Retorna None si no se encuentra
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM cortes_caja WHERE id = ?
        ''', (corte_id,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            columnas = ['id', 'fecha_hora', 'efectivo_inicial', 'efectivo_final',
                       'ventas_efectivo', 'ventas_tarjeta', 'ventas_transferencia',
                       'retiros', 'notas', 'created_at']
            return dict(zip(columnas, resultado))
        return None

    def listar_cortes(self, fecha_inicio: str = None, fecha_fin: str = None) -> List[Dict]:
        """
        Listar todos los cortes de caja
        Opcionalmente filtrar por rango de fechas
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM cortes_caja"
        params = []
        
        if fecha_inicio and fecha_fin:
            query += " WHERE fecha_hora BETWEEN ? AND ?"
            params = [fecha_inicio, fecha_fin]
        
        query += " ORDER BY fecha_hora DESC"
        cursor.execute(query, params)
        
        resultados = cursor.fetchall()
        conn.close()
        
        columnas = ['id', 'fecha_hora', 'efectivo_inicial', 'efectivo_final',
                   'ventas_efectivo', 'ventas_tarjeta', 'ventas_transferencia',
                   'retiros', 'notas', 'created_at']
        
        return [dict(zip(columnas, row)) for row in resultados]

    def actualizar_corte(self, corte_id: int, **kwargs) -> bool:
        """
        Actualizar un corte de caja existente
        Retorna True si se actualizó correctamente
        """
        campos_permitidos = {
            'efectivo_inicial', 'efectivo_final', 'ventas_efectivo',
            'ventas_tarjeta', 'ventas_transferencia', 'retiros', 'notas'
        }
        
        actualizaciones = {k: v for k, v in kwargs.items() if k in campos_permitidos}
        if not actualizaciones:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "UPDATE cortes_caja SET " + \
                ", ".join(f"{k} = ?" for k in actualizaciones.keys()) + \
                " WHERE id = ?"
        
        valores = list(actualizaciones.values()) + [corte_id]
        cursor.execute(query, valores)
        
        exito = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return exito

    def eliminar_corte(self, corte_id: int) -> bool:
        """
        Eliminar un corte de caja
        Retorna True si se eliminó correctamente
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cortes_caja WHERE id = ?', (corte_id,))
        
        exito = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return exito

# Ejemplo de uso
if __name__ == "__main__":
    # Crear una instancia de la clase
    cortes = CorteCaja()
    
    # Ejemplo de crear un nuevo corte
    nuevo_corte = cortes.crear_corte(
        efectivo_inicial=1000.0,
        efectivo_final=2500.0,
        ventas_efectivo=1800.0,
        ventas_tarjeta=500.0,
        ventas_transferencia=200.0,
        retiros=1000.0,
        notas="Corte de prueba"
    )
    print(f"Nuevo corte creado con ID: {nuevo_corte}")
    
    # Obtener el corte creado
    corte = cortes.obtener_corte(nuevo_corte)
    print("Corte obtenido:", corte)
    
    # Listar todos los cortes
    todos_cortes = cortes.listar_cortes()
    print("Total de cortes:", len(todos_cortes))
