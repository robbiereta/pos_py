import cv2
import pytesseract
import pandas as pd
from datetime import datetime
import os
from PIL import Image
import numpy as np

def process_invoice_image(image_path):
    """
    Process an invoice image and extract text using OCR
    """
    # Read the image
    image = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding to preprocess the image
    threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # Perform OCR on the image
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(threshold, config=custom_config)
    
    # Split the text into lines
    lines = text.split('\n')
    
    # Extract header information
    header = {}
    client = {}
    items = []
    
    # Process lines
    current_section = 'header'
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Try to identify sections based on content
        if 'RFC:' in line or 'R.F.C.' in line:
            current_section = 'header'
            header['RFC'] = line.split(':')[-1].strip()
        elif 'DIRECCIÓN:' in line or 'DIRECCION:' in line:
            current_section = 'client'
            client['Direccion'] = line.split(':')[-1].strip()
        elif any(word in line.upper() for word in ['CÓDIGO', 'CANTIDAD', 'PRECIO', 'IMPORTE']):
            current_section = 'items'
            continue
            
        # Process line based on current section
        if current_section == 'items':
            # Try to parse item line
            parts = line.split()
            if len(parts) >= 4:  # Assuming minimum: code, description, quantity, price
                try:
                    item = {
                        'Código': parts[0],
                        'Descripción': ' '.join(parts[1:-3]),
                        'Cantidad': float(parts[-3].replace(',', '')),
                        'Precio': float(parts[-2].replace(',', '')),
                        'Importe': float(parts[-1].replace(',', ''))
                    }
                    items.append(item)
                except (ValueError, IndexError):
                    pass

    # Create DataFrame
    df = pd.DataFrame(items)
    
    # Generate filename
    filename = f'invoice_ocr_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    # Create Excel writer
    writer = pd.ExcelWriter(filename, engine='openpyxl')
    
    # Write header information if available
    if header:
        df_header = pd.DataFrame([header])
        df_header.to_excel(writer, sheet_name='Invoice', index=False, startrow=0)
    
    # Write client information if available
    if client:
        df_client = pd.DataFrame([client])
        df_client.to_excel(writer, sheet_name='Invoice', index=False, startrow=len(header) + 2)
    
    # Write items
    start_row = len(header) + len(client) + 4 if header and client else 0
    df.to_excel(writer, sheet_name='Invoice', index=False, startrow=start_row)
    
    # Save the file
    writer.close()
    
    return filename

def main():
    # Check if image path is provided
    image_path = input("Please enter the path to the invoice image: ")
    
    if not os.path.exists(image_path):
        print(f"Error: File {image_path} does not exist")
        return
    
    try:
        filename = process_invoice_image(image_path)
        print(f"Excel file created: {filename}")
    except Exception as e:
        print(f"Error processing image: {str(e)}")

if __name__ == "__main__":
    main()
