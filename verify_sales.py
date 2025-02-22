from convertir_ventas import create_app
from datetime import datetime

def verify_sales_data():
    try:
        app = create_app()
        with app.app_context():
            # Count total sales
            total_sales = app.db.sales.count_documents({})
            print(f"\nTotal sales in database: {total_sales}")
            
            # Get sales statistics
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_amount": {"$sum": "$total_amount"},
                        "min_amount": {"$min": "$total_amount"},
                        "max_amount": {"$max": "$total_amount"},
                        "avg_amount": {"$avg": "$total_amount"}
                    }
                }
            ]
            stats = list(app.db.sales.aggregate(pipeline))
            if stats:
                stats = stats[0]
                print(f"\nSales Statistics:")
                print(f"Total Amount: ${stats['total_amount']:,.2f}")
                print(f"Min Amount: ${stats['min_amount']:,.2f}")
                print(f"Max Amount: ${stats['max_amount']:,.2f}")
                print(f"Average Amount: ${stats['avg_amount']:,.2f}")
            
            # Get sales by date
            pipeline = [
                {
                    "$group": {
                        "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
                        "total": {"$sum": "$total_amount"},
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            sales_by_date = list(app.db.sales.aggregate(pipeline))
            
            print("\nSales by Date:")
            for day in sales_by_date:
                print(f"{day['_id']}: ${day['total']:,.2f} ({day['count']} sales)")
            
            # Get some details about the products
            print("\nProduct Information:")
            products = list(app.db.products.find())
            print(f"Total unique products: {len(products)}")
            if products:
                print("\nSample products:")
                for product in products[:3]:
                    print(f"- {product.get('name', 'N/A')} (${product.get('price', 0):,.2f})")
            
    except Exception as e:
        print('Error:', str(e))

if __name__ == '__main__':
    verify_sales_data()
