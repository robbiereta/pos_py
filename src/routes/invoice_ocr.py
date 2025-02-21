import os
from flask import Blueprint, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
from src.services.process_invoice_image import process_invoice_image
from src.services.convert_invoice import convert_to_excel

invoice_ocr_bp = Blueprint('invoice_ocr', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@invoice_ocr_bp.route('/invoice-ocr', methods=['GET', 'POST'])
def invoice_ocr():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            try:
                # Save the file temporarily
                filename = secure_filename(file.filename)
                temp_path = os.path.join('data/temp', filename)
                file.save(temp_path)
                
                # Process the image
                extracted_data = process_invoice_image(temp_path)
                
                # Convert to Excel
                excel_path = convert_to_excel(extracted_data)
                
                # Clean up temporary file
                os.remove(temp_path)
                
                # Send Excel file
                return send_file(
                    excel_path,
                    as_attachment=True,
                    download_name='invoice_conversion.xlsx'
                )
            except Exception as e:
                return jsonify({'error': str(e)}), 500
            finally:
                # Clean up Excel file
                if 'excel_path' in locals() and os.path.exists(excel_path):
                    os.remove(excel_path)
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    return render_template('invoice_ocr.html')
