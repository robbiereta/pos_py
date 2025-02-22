from convertir_ventas import create_app

def clear_sales():
    try:
        app = create_app()
        with app.app_context():
            result = app.db.sales.delete_many({})
            print(f"Deleted {result.deleted_count} sales records")
    except Exception as e:
        print('Error:', str(e))

if __name__ == '__main__':
    clear_sales()
