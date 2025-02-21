import pandas as pd
from datetime import datetime

def extract_invoice_data(text):
    # Split text into lines
    lines = text.split('\n')
    
    # Initialize lists to store item data
    items = []
    
    # Process each line
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
            
        # Try to parse product lines
        parts = line.split()
        if len(parts) >= 4:
            try:
                # Find the index of Pza/Par/Pllo/Kit
                unit_index = -1
                for i, part in enumerate(parts):
                    if part in ['Pza', 'Par', 'Pllo', 'Kit']:
                        unit_index = i
                        break
                
                if unit_index > 0:
                    code = parts[0]
                    description = ' '.join(parts[1:unit_index-2])  # Everything up to the box number
                    box_number = int(parts[unit_index-2])  # This is the box number
                    pieces = float(parts[unit_index-1].replace(',', ''))
                    unit = parts[unit_index]
                    price = float(parts[unit_index+1].replace('$', ''))
                    total = float(parts[unit_index+2].replace('$', ''))
                    
                    items.append({
                        'Código': code,
                        'Descripción': description,
                        'No. Caja': box_number,
                        'Piezas': pieces,
                        'Unidad': unit,
                        'Precio': price,
                        'Importe': total
                    })
            except Exception as e:
                print(f"Error processing line: {line}")
                print(f"Error: {str(e)}")
                continue

    return items

def save_to_excel(items, output_file='invoice_conversion.xlsx'):
    # Create DataFrame
    df = pd.DataFrame(items)
    
    # Calculate totals
    total = sum(item['Importe'] for item in items)
    
    # Save to Excel
    df.to_excel(output_file, index=False)
    
    print(f"Excel file created: {output_file}")
    print(f"Total amount: ${total:.2f}")

def main():
    # Sample invoice text from the images
    invoice_text = """
    LL102 LLANTA 18 X 2.10 NEGRA CROSS NHL 3 10,000 Pza $51.21 $512.11
    LL275 LLANTA 24 X 1 3/8 BICOLOR V-RUBBER VRB015 2 8,000 Pza $106.26 $527.53
    LL488 LLANTA 24 X 2.125 NGA MTB "ROUND-BRAND" NAHEL 1 10,000 Pza $57.51 $575.11
    LL345W LLANTA 26 X 1 3/8 BICOLOR NHL 1 5,000 Pza $97.78 $586.68
    P105-G PIÑON PASOS 14/28 C-BALAS CAFE -ALTREGO- 7 10,000 Pza $47.80 $478.02
    P124-GOODE PIÑON PASOS 14/28 CHINO C-BALAS BRONCE -ALTREGO- 7 15,000 Pza $52.26 $784.24
    """
    
    # Process the invoice text
    items = extract_invoice_data(invoice_text)
    
    # Save to Excel with timestamp
    filename = f'invoice_conversion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    save_to_excel(items, filename)

if __name__ == "__main__":
    main()
