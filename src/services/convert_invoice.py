import os
from datetime import datetime
import pandas as pd
import pytesseract
from PIL import Image

def process_invoice_image(image_path):
    """Process an invoice image using OCR and return extracted data."""
    try:
        # Open the image
        image = Image.open(image_path)
        
        # Use pytesseract to extract text
        text = pytesseract.image_to_string(image, lang='spa')
        
        # Process the extracted text to get structured data
        # This is a simplified example - you would need to add more sophisticated parsing
        lines = text.split('\n')
        data = []
        
        for line in lines:
            if line.strip():  # Skip empty lines
                # Try to extract product details
                # This is a basic example - you would need to adapt it to your invoice format
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        # Attempt to find a price in the line
                        price = next((float(p.replace('$', '').replace(',', '')) 
                                   for p in parts if p.startswith('$')), None)
                        if price:
                            data.append({
                                'Description': ' '.join(parts[:-1]),
                                'Price': price
                            })
                    except ValueError:
                        continue
        
        return data
    
    except Exception as e:
        raise Exception(f"Error processing invoice: {str(e)}")

def convert_to_excel(data, output_dir=None):
    """Convert extracted data to Excel format."""
    try:
        if not data:
            raise ValueError("No data to convert")
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Calculate total
        total = df['Price'].sum()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"invoice_conversion_{timestamp}.xlsx"
        
        if output_dir:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            filepath = os.path.join(output_dir, filename)
        else:
            filepath = filename
        
        # Create Excel writer
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Write data
            df.to_excel(writer, sheet_name='Invoice Details', index=False)
            
            # Get the worksheet
            worksheet = writer.sheets['Invoice Details']
            
            # Add total row
            total_row = len(df) + 2
            worksheet.cell(row=total_row, column=1, value='Total')
            worksheet.cell(row=total_row, column=2, value=total)
        
        print(f"Excel file created: {filename}")
        print(f"Total amount: ${total:,.2f}")
        
        return filepath
        
    except Exception as e:
        raise Exception(f"Error converting to Excel: {str(e)}")

# Invoice header data
header = {
    'Vendedor': 'ELIZABETH PEREZ LOPEZ',
    'Dirección': 'CARR. TAMPICO-MANTE 812 COL. LAS AMERICAS',
    'Ciudad': 'TAMPICO, TAMPS. CP. 89336',
    'RFC': 'PELE840717CG9',
    'CURP': 'PELE840717'
}

# Cliente data
client = {
    'Nombre': 'ALMA ALICIA FLORES ZAVALA',
    'Dirección': 'AV. CARRERA TORRES 742',
    'Colonia': 'HEROE DE NACOZARI',
    'Ciudad': 'Cd Victoria, Tamps.',
    'CP': '87030',
    'RFC': 'FOZA880125TC2'
}

# Invoice items
items = [
    {'Código': 'ZXKF14020030', 'Descripción': 'ZAPATA ITALIKA(3X19/DXT150/FT150/FT150-G1-01)', 'Cantidad': 3, 'Unidad': 'Pza', 'Precio': 87.94, 'Importe': 263.82},
    {'Código': 'ZXXF104020531', 'Descripción': 'JUEGO DE ESPEJOS ITALIKA P150Z2/150Z2/170Z2/502)', 'Cantidad': 2, 'Unidad': 'Jgo', 'Precio': 79.35, 'Importe': 158.70},
    {'Código': 'ZXXF10010038', 'Descripción': 'JUEGO DE ESPEJOS ITALIKA P150Z2/150Z2/170Z2/502)', 'Cantidad': 5, 'Unidad': 'Jgo', 'Precio': 94.79, 'Importe': 473.95},
    {'Código': 'ZXXF06010049', 'Descripción': 'JUEGO DE ESPEJOS ITALIKA P DM200/DM125/DM150 SPORT)', 'Cantidad': 20, 'Unidad': 'Pza', 'Precio': 10.54, 'Importe': 210.80},
    {'Código': 'ZTD3115', 'Descripción': 'BALERO P MOTO 6201 C/TAPAS (MIKADO072500)', 'Cantidad': 4, 'Unidad': 'Pza', 'Precio': 303.64, 'Importe': 1214.56},
    {'Código': 'ZXXF025021', 'Descripción': 'TAPAS EMBRAGUE ITALIKA CB125/CB125G/WS150/VS150', 'Cantidad': 20, 'Unidad': 'Pza', 'Precio': 8.72, 'Importe': 174.40},
    {'Código': 'ZXXF04030023', 'Descripción': 'CHICOTE DE FRENO DELANTERO FT125 CLASICA', 'Cantidad': 2, 'Unidad': 'Jgo', 'Precio': 195.56, 'Importe': 391.12},
    {'Código': 'ZZPEMP-028', 'Descripción': 'EMPAQUE DE MOTOR P ITALIKA 250Z/FT250/TC250/VARIAS', 'Cantidad': 4, 'Unidad': 'Jgo', 'Precio': 149.71, 'Importe': 598.84},
    {'Código': 'ZZPED-B007', 'Descripción': 'PEDAL DE FRENO CHOP WT110/XT110/RT110/RT110/RT', 'Cantidad': 2, 'Unidad': 'Pza', 'Precio': 54.83, 'Importe': 109.66},
    {'Código': 'CA011', 'Descripción': 'CABLE CLUTCH P/MOTOCICLETA (P/N:CALG0050000)', 'Cantidad': 5, 'Unidad': 'Pza', 'Precio': 162.45, 'Importe': 812.25},
    {'Código': 'ZZIAC-005', 'Descripción': 'AJUSTADOR TENSOR DE CADENA FT125 DT125 CLASICA', 'Cantidad': 10, 'Unidad': 'Jgo', 'Precio': 10.72, 'Importe': 107.20},
    {'Código': 'ZY-CM250351', 'Descripción': 'CANDADO CADENA 520 (PROX)', 'Cantidad': 2, 'Unidad': 'Pza', 'Precio': 184.49, 'Importe': 368.98},
    {'Código': 'ZY-CM250351024', 'Descripción': 'CANDADO CADENA PASO 520 (PROX)', 'Cantidad': 5, 'Unidad': 'Pza', 'Precio': 4.11, 'Importe': 20.55},
    {'Código': 'ZXXF15010249', 'Descripción': 'LLANTA ITALIKA "CITY ROAD" 2.50-17 (TT)', 'Cantidad': 1, 'Unidad': 'Pza', 'Precio': 244.44, 'Importe': 244.44},
    {'Código': 'ZZMOTG014', 'Descripción': 'BUJES DE SHOCK TRAS DE NYLON VARIAS MOTOS DE', 'Cantidad': 10, 'Unidad': 'Jgo', 'Precio': 27.16, 'Importe': 271.60},
    {'Código': 'ZY-FLA4021003', 'Descripción': 'FUNDA ASIENTO G7 NEGRA (XL=114X53CM) COOL MESH P', 'Cantidad': 10, 'Unidad': 'Pza', 'Precio': 74.69, 'Importe': 746.90},
    {'Código': 'ZZKSP-F23', 'Descripción': 'PISTON SPROCKET PHUB SP115T CICLO 42BH10BL P ITALIKA', 'Cantidad': 1, 'Unidad': 'Kit', 'Precio': 168.20, 'Importe': 168.20},
    {'Código': 'ZXXF15010250', 'Descripción': 'CAMARA ITALIKA 2.50Z-75 X 17 CITY ROAD', 'Cantidad': 50, 'Unidad': 'Pza', 'Precio': 35.27, 'Importe': 1763.50},
    {'Código': 'ZZCAM-017F', 'Descripción': 'CAMARA MOTO 4.10-X 18 TR4 KIRUS ALESSIA', 'Cantidad': 20, 'Unidad': 'Pza', 'Precio': 59.75, 'Importe': 1195.00},
    {'Código': 'MA154-11TT', 'Descripción': 'MANUBRIO BKT-HUNTER-ACERO L=875 R=5.5 COL INGO', 'Cantidad': 4, 'Unidad': 'Pza', 'Precio': 175.66, 'Importe': 702.64},
    {'Código': 'ZXXED1020016', 'Descripción': 'KIT CARBURADOR P ITALIKA RC150 09-17', 'Cantidad': 5, 'Unidad': 'Pza', 'Precio': 8.07, 'Importe': 40.35},
    {'Código': 'ZZBAL-6004-2RS', 'Descripción': 'BALERO 6004 2RS C/TAPAS P ATV150/250/RT125/DS150', 'Cantidad': 10, 'Unidad': 'Pza', 'Precio': 16.97, 'Importe': 169.70}
]

# Create DataFrame
df = pd.DataFrame(items)

# Calculate totals
total = sum(item['Importe'] for item in items)

# Create Excel writer
filename = f'invoice_conversion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
writer = pd.ExcelWriter(filename, engine='openpyxl')

# Write header information
df_header = pd.DataFrame([header])
df_header.to_excel(writer, sheet_name='Invoice', index=False, startrow=0)

# Write client information
df_client = pd.DataFrame([client])
df_client.to_excel(writer, sheet_name='Invoice', index=False, startrow=len(header) + 2)

# Write items
df.to_excel(writer, sheet_name='Invoice', index=False, startrow=len(header) + len(client) + 4)

# Save the file
writer.close()

print(f"Excel file created: {filename}")
print(f"Total amount: ${total:.2f}")
