from datetime import datetime
from bson import ObjectId

class CorteCajaMongo:
    def __init__(self, db):
        """
        Inicializa el manejador de cortes de caja
        db: instancia de la base de datos MongoDB
        """
        self.db = db
        self.collection = db.cortes_caja

    def crear_corte(self, monto_inicial, monto_final, ventas_efectivo=0, 
                   ventas_tarjeta=0, ventas_transferencia=0, retiros=0, notas=""):
        """
        Crea un nuevo corte de caja
        """
        corte = {
            'fecha_hora': datetime.now(),
            'monto_inicial': float(monto_inicial),
            'monto_final': float(monto_final),
            'ventas_efectivo': float(ventas_efectivo),
            'ventas_tarjeta': float(ventas_tarjeta),
            'ventas_transferencia': float(ventas_transferencia),
            'retiros': float(retiros),
            'notas': notas
        }
        
        result = self.collection.insert_one(corte)
        return str(result.inserted_id)

    def obtener_corte(self, corte_id):
        """
        Obtiene un corte de caja por su ID
        """
        return self.collection.find_one({'_id': ObjectId(corte_id)})

    def obtener_cortes(self, fecha_inicio=None, fecha_fin=None):
        """
        Obtiene los cortes de caja en un rango de fechas
        Si no se especifican fechas, retorna todos los cortes
        """
        query = {}
        if fecha_inicio and fecha_fin:
            query['fecha_hora'] = {
                '$gte': fecha_inicio,
                '$lte': fecha_fin
            }
        
        return list(self.collection.find(query).sort('fecha_hora', -1))

    def actualizar_corte(self, corte_id, **kwargs):
        """
        Actualiza un corte de caja
        """
        updates = {}
        valid_fields = ['monto_inicial', 'monto_final', 'ventas_efectivo', 
                       'ventas_tarjeta', 'ventas_transferencia', 'retiros', 'notas']
        
        for field in valid_fields:
            if field in kwargs:
                if field in ['monto_inicial', 'monto_final', 'ventas_efectivo', 
                           'ventas_tarjeta', 'ventas_transferencia', 'retiros']:
                    updates[field] = float(kwargs[field])
                else:
                    updates[field] = kwargs[field]
        
        if updates:
            result = self.collection.update_one(
                {'_id': ObjectId(corte_id)},
                {'$set': updates}
            )
            return result.modified_count > 0
        return False

    def eliminar_corte(self, corte_id):
        """
        Elimina un corte de caja
        """
        result = self.collection.delete_one({'_id': ObjectId(corte_id)})
        return result.deleted_count > 0

    def obtener_ultimo_corte(self):
        """
        Obtiene el último corte de caja registrado
        """
        return self.collection.find_one(sort=[('fecha_hora', -1)])

    def obtener_cortes_del_mes(self, año, mes):
        """
        Obtiene todos los cortes de un mes específico
        """
        inicio_mes = datetime(año, mes, 1)
        if mes == 12:
            fin_mes = datetime(año + 1, 1, 1)
        else:
            fin_mes = datetime(año, mes + 1, 1)
        
        return list(self.collection.find({
            'fecha_hora': {
                '$gte': inicio_mes,
                '$lt': fin_mes
            }
        }).sort('fecha_hora', 1))

    def calcular_totales_del_mes(self, año, mes):
        """
        Calcula los totales de ventas y retiros para un mes específico
        """
        cortes = self.obtener_cortes_del_mes(año, mes)
        
        totales = {
            'ventas_efectivo': 0,
            'ventas_tarjeta': 0,
            'ventas_transferencia': 0,
            'total_ventas': 0,
            'retiros': 0,
            'num_cortes': len(cortes)
        }
        
        for corte in cortes:
            totales['ventas_efectivo'] += corte['ventas_efectivo']
            totales['ventas_tarjeta'] += corte['ventas_tarjeta']
            totales['ventas_transferencia'] += corte['ventas_transferencia']
            totales['retiros'] += corte['retiros']
        
        totales['total_ventas'] = (
            totales['ventas_efectivo'] + 
            totales['ventas_tarjeta'] + 
            totales['ventas_transferencia']
        )
        
        return totales
