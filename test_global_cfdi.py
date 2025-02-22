from cfdi_generator import cfdi_generator_prod
from datetime import datetime

# Sample sales data
sales = [
    {'_id': '1', 'total_amount': 100.00},
    {'_id': '2', 'total_amount': 150.00},
    {'_id': '3', 'total_amount': 200.00}
]

# Current date for the global CFDI
current_date = datetime(2025, 2, 22, 12, 45, 38)

try:
    # Generate global CFDI in production mode
    result = cfdi_generator_prod.generate_global_cfdi(sales, current_date)
    
    print("\nGlobal CFDI generated successfully!")
    print(f"UUID: {result['uuid']}")
    print(f"Folio: {result['folio']}")
    print("XML length:", len(result['xml']))
    
except Exception as e:
    print(f"Error generating global CFDI: {e}")
    # Print more detailed error information if available
    if hasattr(e, 'response') and hasattr(e.response, 'text'):
        print("Detailed error:", e.response.text)
