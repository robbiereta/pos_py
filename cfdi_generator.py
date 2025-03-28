import requests
from models import Invoice, GlobalInvoice, Issuer, NominaInvoice
import os
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CFDIGenerator:
    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.url =os.getenv('SW_URL', 'http://services.test.sw.com.mx')
        self.token = os.getenv('SW_TOKEN')
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/jsontoxml'
        }

    def _prepare_emisor(self):
        emisor_data = {
            "Rfc": os.getenv('SAT_RFC'),
            "Nombre": os.getenv('SAT_NOMBRE'),
            "RegimenFiscal": os.getenv('SAT_REGIMEN_FISCAL')
        }
        # Validate required fields
        if not all([emisor_data['Rfc'], emisor_data['Nombre'], emisor_data['RegimenFiscal']]):
            raise ValueError("Missing required emisor data in environment variables")
        return emisor_data

    def _prepare_receptor(self, is_public=False):
        """Prepare receptor (customer) data for CFDI"""
        if is_public:
            return {
                "Rfc": "XAXX010101000",
                "Nombre": "PUBLICO EN GENERAL",
                "DomicilioFiscalReceptor": os.getenv('SAT_CP'),
                "RegimenFiscalReceptor": "616",
                "UsoCFDI": "S01"  # Changed from G03 to S01 for global invoices
            }
        else:
            receptor_data = {
                "Rfc": os.getenv('RECEPTOR_RFC'),
                "Nombre": os.getenv('RECEPTOR_NOMBRE'),
                "UsoCFDI": "S01", 
                "RegimenFiscalReceptor": "616",  # Sin obligaciones fiscales
                "DomicilioFiscalReceptor": os.getenv('SAT_CP')
            }
            # Validate required fields
            if not all([receptor_data['Rfc'], receptor_data['Nombre']]):
                raise ValueError("Missing required receptor data in environment variables")
            return receptor_data

    def _prepare_conceptos(self, sales):
        """Prepare conceptos (line items) for CFDI"""
        conceptos = []
        for sale in sales:
            # Extract subtotal from total (VAT is included)
            total_amount = float(sale['total_amount'])
            subtotal = round(total_amount / 1.16, 2)
            tax_amount = round(total_amount - subtotal, 2)
            
            # Get sale details if available
            sale_details = []
            if 'details' in sale:
                for detail in sale['details']:
                    product_name = detail.get('product_name', 'Producto')
                    quantity = detail.get('quantity', 1)
                    sale_details.append(f"{quantity}x {product_name}")
            
           
            
            concepto = {
                "ClaveProdServ": "01010101",  # No existe en el catálogo
                "NoIdentificacion": str(sale['_id']),
                "Cantidad": 1,
                "ClaveUnidad": "ACT",
                "Descripcion": "Venta",
                "ValorUnitario": f"{subtotal:.2f}",
                "Importe": f"{subtotal:.2f}",
                "ObjetoImp": "02",
                "Impuestos": {
                    "Traslados": [
                        {
                            "Base": f"{subtotal:.2f}",
                            "Impuesto": "002",  # IVA
                            "TipoFactor": "Tasa",
                            "TasaOCuota": "0.160000",
                            "Importe": f"{tax_amount:.2f}"
                        }
                    ]
                }
            }
            conceptos.append(concepto)
        return conceptos

    def _prepare_impuestos(self, subtotal, tax_amount):
        """Prepare impuestos (taxes) section for CFDI"""
        return {
            "TotalImpuestosTrasladados": f"{tax_amount:.2f}",
            "Traslados": [
                {
                    "Base": f"{subtotal:.2f}",
                    "Impuesto": "002",  # IVA
                    "TipoFactor": "Tasa",
                    "TasaOCuota": "0.160000",
                    "Importe": f"{tax_amount:.2f}"
                }
            ]
        }

    def _save_cfdi_json(self, comprobante, prefix="cfdi"):
        """Save CFDI JSON to file for debugging"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(comprobante, f, indent=2, ensure_ascii=False)
            
            print(f"\nCFDI JSON guardado en: {filename}")
            return filename
        except Exception as e:
            print(f"Error al guardar JSON: {str(e)}")
            return None

    def _call_sw_sapien_api(self, comprobante):
        """Call SW Sapien API to stamp CFDI"""
        try:
            # Guardar JSON para debugging
            self._save_cfdi_json(comprobante)

            # En modo producción, llamar al PAC
            endpoint = "/v3/cfdi33/issue/json/v4"
            url = f"{self.url}{endpoint}"
            
            print(f"\nLlamando a API del PAC:")
            print(f"URL: {url}")
            print(f"Headers: {json.dumps(self.headers, indent=2)}")
            print(f"Request: {json.dumps(comprobante, indent=2)}")
            
            response = requests.post(
                url,
                headers=self.headers,
                json=comprobante
            )
            
            print(f"\nRespuesta del PAC:")
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Body: {response.text}")
            
            try:
                response_json = response.json()
                print(f"Response JSON: {json.dumps(response_json, indent=2)}")
                if response.status_code == 200:
                    return response_json
                else:
                    raise Exception(f"Error calling PAC API: {json.dumps(response_json, indent=2)}")
            except json.JSONDecodeError:
                raise Exception(f"Invalid JSON response from PAC: {response.text}")
        except Exception as e:
            print(f"Error in _call_sw_sapien_api: {str(e)}")
            raise
     
    def list_cfdis(self, start_date=None, end_date=None):
        """List CFDIs from the PAC within a date range"""
        try:
            if self.test_mode:
                return {
                    'status': 'success',
                    'data': {
                        'cfdi': []
                    }
                }
            
            params = {}
            if start_date:
                params['fechaInicial'] = start_date.strftime("%Y-%m-%d")
            if end_date:
                params['fechaFinal'] = end_date.strftime("%Y-%m-%d")
            
            response = requests.get(
                f"{self.url}/v4/cfdi33/list",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data
                else:
                    raise Exception(f"API Error: {data.get('message', 'Unknown error')}")
            else:
                raise Exception(f"HTTP Error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request Error: {str(e)}")

    def generate_cfdi(self, sale):
        """Generate CFDI for a single sale"""
        try:
            comprobante = {
                "Version": "4.0",
                "Serie": "A",
                "Folio": str(sale['_id']),
                "Fecha": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
                "FormaPago": "01",  # Efectivo
                "SubTotal": f"{sale['total_amount']:.2f}",
                "Moneda": "MXN",
                "Total": f"{sale['total_amount'] * 1.16:.2f}",  # Including IVA
                "TipoDeComprobante": "I",  # Ingreso
                "Exportacion": "01",  # No aplica
                "MetodoPago": "PUE",  # Pago en una sola exhibición
                "LugarExpedicion": os.getenv('SAT_CP'),
                "Emisor": self._prepare_emisor(),
                "Receptor": self._prepare_receptor(True),
                "Conceptos": self._prepare_conceptos([sale])
            }
            
            result = self._call_sw_sapien_api(comprobante)
            
            # Create invoice record
            invoice = Invoice(
                sale_id=sale['_id'],
                cfdi_uuid=result['data']['uuid'],
                xml_content=result['data']['cfdi']
            )
            # db.session.add(invoice)
            # sale.is_invoiced = True
            # db.session.commit()
            
            return result
            
        except Exception as e:
            raise Exception(f"Error generating CFDI: {str(e)}")

    def _get_next_global_folio(self):
        """Get next available folio for global invoices"""
        try:
            # Get last folio from database
            # result = db.session.query(GlobalInvoice.folio)\
            #     .order_by(GlobalInvoice.folio.desc())\
            #     .first()
            
            # if result and result[0]:
            #     last_folio = int(result[0])
            #     return str(last_folio + 1).zfill(6)  # Format: 000001, 000002, etc.
            return "000001"  # First folio
        except Exception as e:
            print(f"Error getting next folio: {str(e)}")
            return "000001"

    def generate_global_cfdi(self, sales, date):
        """Generate a global CFDI for multiple sales"""
        try:
            # First prepare concepts to get exact tax amounts
            conceptos = self._prepare_conceptos(sales)
            
            # Calculate totals from concepts to ensure consistency
            subtotal = sum(float(concepto['Importe']) for concepto in conceptos)
            total_tax = sum(float(traslado['Importe']) 
                          for concepto in conceptos 
                          for traslado in concepto['Impuestos']['Traslados'])
            total_amount = round(subtotal + total_tax, 2)
            
            # Get next folio
            folio = self._get_next_global_folio()
            
            # Prepare CFDI
            comprobante = {
                "Version": "4.0",
                "Serie": "G",  # Factura Global
                "Folio": folio,
                "Fecha": date.strftime("%Y-%m-%dT%H:%M:%S"),
                "Sello": "",
                "FormaPago": "99",
                "NoCertificado": "",
                "Certificado": "",
                "SubTotal": f"{subtotal:.2f}",
                "Moneda": "MXN",
                "Total": f"{total_amount:.2f}",
                "TipoDeComprobante": "I",  # Ingreso
                "Exportacion": "01",  # No aplica
                "MetodoPago": "PUE",  # Pago en una sola exhibición
                "LugarExpedicion": os.getenv('SAT_CP'),
                "InformacionGlobal": {
                    "Periodicidad": "02",
                    "Meses": date.strftime("%m"),
                    "Año": date.strftime("%Y")
                },
                "Emisor": self._prepare_emisor(),
                "Receptor": self._prepare_receptor(True),
                "Conceptos": conceptos,
                "Impuestos": self._prepare_impuestos(subtotal, total_tax)
            }
            
            if self.test_mode:
                # En modo prueba, solo devolver un resultado simulado
                print("\nModo prueba - Simulando timbrado de CFDI")
                self._save_cfdi_json(comprobante, "global_cfdi")
                test_uuid = f'TEST-UUID-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
                return {
                    'uuid': test_uuid,
                    'folio': folio,
                    'xml': '<xml>Test XML Content</xml>'
                }
            
            # Call PAC API
            result = self._call_sw_sapien_api(comprobante)
            
            return {
                'uuid': result['data']['uuid'],
                'folio': folio,
                'xml': result['data']['cfdi']
            }
            
        except Exception as e:
            raise Exception(f"Error generating Global CFDI: {str(e)}")

  
# Example usage
cfdi_generator = CFDIGenerator(test_mode=False)
example_cfdi_data = {
    "emisor": cfdi_generator._prepare_emisor(),
    "receptor": cfdi_generator._prepare_receptor(),
    "conceptos": [],  # Add your concepts here
    "total": 100.0,
    "subtotal": 100.0,
    "impuestos": {
        "totalImpuestosTrasladados": 0.0,
        "traslados": []
    }
}

