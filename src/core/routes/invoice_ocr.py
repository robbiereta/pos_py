from flask import Blueprint, render_template, request, send_file, current_app
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import cv2
import pytesseract
import pandas as pd
from io import BytesIO
import numpy as np
from PIL import Image

invoice_ocr_bp = Blueprint('invoice_ocr', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
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
    
    output.seek(0)
    return output

@invoice_ocr_bp.route('/invoice-ocr', methods=['GET', 'POST'])
def invoice_ocr():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return render_template('invoice_ocr.html', error='No file part')
        
        file = request.files['file']
        
        # if user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            return render_template('invoice_ocr.html', error='No selected file')
        
        if file and allowed_file(file.filename):
            # Create a temporary directory if it doesn't exist
            temp_dir = os.path.join(current_app.root_path, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Save the file temporarily
            filename = secure_filename(file.filename)
            temp_path = os.path.join(temp_dir, filename)
            file.save(temp_path)
            
            try:
                # Process the image
                excel_output = process_invoice_image(temp_path)
                
                # Remove temporary file
                os.remove(temp_path)
                
                # Generate output filename
                output_filename = f'invoice_ocr_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
                
                # Return the Excel file
                return send_file(
                    excel_output,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=output_filename
                )
            
            except Exception as e:
                # Remove temporary file in case of error
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return render_template('invoice_ocr.html', error=str(e))
            
        return render_template('invoice_ocr.html', error='Invalid file type')
    
    return render_template('invoice_ocr.html')
