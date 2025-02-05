import requests
from models import Invoice, db, GlobalInvoice
import os
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CFDIGenerator:
    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.url = os.getenv('SW_URL', 'http://services.test.sw.com.mx')
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
        """Prepare conceptos for CFDI, each sale is a separate concepto"""
        conceptos = []
        for sale in sales:
            # Extract subtotal from total (VAT is included)
            subtotal = round(sale.total_amount / 1.16, 2)
            tax_amount = round(sale.total_amount - subtotal, 2)
            
            # Obtener productos de la venta
            try:
                productos = sale.products
                if isinstance(productos, list):
                    descripcion = ", ".join([f"{p.get('quantity', 1)}x {p.get('name', 'Producto')}" for p in productos])
                elif isinstance(productos, dict):
                    descripcion = ", ".join([f"{qty}x {name}" for name, qty in productos.items()])
                else:
                    descripcion = "Venta"
            except Exception as e:
                print(f"Error al procesar productos de venta {sale.id}: {str(e)}")
                descripcion = f"Venta"
            
            concepto = {
                "ClaveProdServ": "01010101",  # No existe en el catálogo
                "NoIdentificacion": str(sale.id),
                "Cantidad": 1,
                "ClaveUnidad": "ACT",  # Actividad
                "Descripcion": descripcion,
                "ValorUnitario": f"{subtotal:.2f}",
                "Importe": f"{subtotal:.2f}",
                "ObjetoImp": "02",  # Sí objeto de impuesto
                "Impuestos": {
                    "Traslados": [
                        {
                            "Base": f"{subtotal:.2f}",
                            "Impuesto": "002",
                            "TipoFactor": "Tasa",
                            "TasaOCuota": "0.160000",
                            "Importe": f"{tax_amount:.2f}"
                        }
                    ]
                }
            }
            conceptos.append(concepto)
        
        return conceptos

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
                "Folio": str(sale.id),
                "Fecha": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
                "FormaPago": "01",  # Efectivo
                "SubTotal": f"{sale.total_amount:.2f}",
                "Moneda": "MXN",
                "Total": f"{sale.total_amount * 1.16:.2f}",  # Including IVA
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
                sale_id=sale.id,
                cfdi_uuid=result['data']['uuid'],
                xml_content=result['data']['cfdi']
            )
            db.session.add(invoice)
            sale.is_invoiced = True
            db.session.commit()
            
            return result
            
        except Exception as e:
            raise Exception(f"Error generating CFDI: {str(e)}")

    def _get_next_global_folio(self):
        """Get next available folio for global invoices"""
        try:
            # Get last folio from database
            result = db.session.query(GlobalInvoice.folio)\
                .order_by(GlobalInvoice.folio.desc())\
                .first()
            
            if result and result[0]:
                last_folio = int(result[0])
                return str(last_folio + 1).zfill(6)  # Format: 000001, 000002, etc.
            return "000001"  # First folio
        except Exception as e:
            print(f"Error getting next folio: {str(e)}")
            return "000001"

    def generate_global_cfdi(self, sales, date):
        """Generate a global CFDI for multiple sales"""
        try:
            # Calculate subtotal and tax for each sale first
            sale_amounts = []
            for sale in sales:
                subtotal = round(sale.total_amount / 1.16, 2)
                tax = round(sale.total_amount - subtotal, 2)
                sale_amounts.append({
                    'subtotal': subtotal,
                    'tax': tax,
                    'total': sale.total_amount
                })

            # Get total amounts
            total_subtotal = sum(amt['subtotal'] for amt in sale_amounts)
            total_tax = sum(amt['tax'] for amt in sale_amounts)
            total_amount = sum(amt['total'] for amt in sale_amounts)

            # Get next folio
            next_folio = self._get_next_global_folio()

            # Prepare CFDI data
            comprobante = {
                "Version": "4.0",
                "Folio": next_folio,
                "Serie": "G",
                "Fecha": date.strftime("%Y-%m-%dT%H:%M:%S"),
                "Sello":"",
                "FormaPago": "99",
                "NoCertificado": "",
                "Certificado": "",
                "SubTotal": f"{total_subtotal:.2f}",
                "Moneda": "MXN",
                "Total": f"{total_amount:.2f}",
                "TipoDeComprobante": "I",
                "Exportacion": "01",
                "MetodoPago": "PUE",
                "LugarExpedicion": os.getenv('SAT_CP'),
                "InformacionGlobal": {
                    "Periodicidad": "04", # Diario
                    "Meses": date.strftime("%m"), # Mes actual
                    "Año": date.strftime("%Y")  # Año actual
                },
                "Emisor": self._prepare_emisor(),
                "Receptor": self._prepare_receptor(),
                "Conceptos": self._prepare_conceptos(sales),
                "Impuestos": {
                    "TotalImpuestosTrasladados": f"{total_tax:.2f}",
                    "Traslados": [
                        {
                            "Base": f"{total_subtotal:.2f}",
                            "Impuesto": "002",
                            "TipoFactor": "Tasa",
                            "TasaOCuota": "0.160000",
                            "Importe": f"{total_tax:.2f}"
                        }
                    ]
                }
            }
            
            # Call SW Sapien API
            return self._call_sw_sapien_api(comprobante)
            
        except Exception as e:
            raise Exception(f"Error generating Global CFDI: {str(e)}")

    def download_xml_from_pac(self, uuid):
        """Download XML directly from PAC using UUID"""
        try:
            response = requests.get(
                f"{self.url}/v4/cfdi/{uuid}/xml",
                headers={'Authorization': f'Bearer {self.token}'}
            )
            
            if response.status_code == 200:
                return response.text
            else:
                error_msg = f"Error al descargar XML del PAC: Status {response.status_code}, Response: {response.text}"
                print(f"PAC Error: {error_msg}")  # Log error for debugging
                raise Exception(error_msg)
                
        except Exception as e:
            error_msg = f"Error al contactar al PAC: {str(e)}"
            print(f"PAC Error: {error_msg}")  # Log error for debugging
            raise Exception(error_msg)

# Create singleton instances for different modes
cfdi_generator = CFDIGenerator(test_mode=True)  # For testing
cfdi_generator_prod = CFDIGenerator(test_mode=False)  # For production
