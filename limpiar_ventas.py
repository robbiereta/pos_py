from convertir_ventas import create_app

def limpiar_ventas():
    app = create_app()
    
    with app.app_context():
        try:
            db = app.db
            result = db.sales.delete_many({})
            print(f"Se eliminaron {result.deleted_count} ventas de la base de datos.")
        except Exception as e:
            print(f"Error al limpiar ventas: {str(e)}")

if __name__ == "__main__":
    limpiar_ventas()
