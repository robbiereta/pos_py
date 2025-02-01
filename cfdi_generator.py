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
            'Content-Type': 'application/json'
        }

    def _prepare_emisor(self):
        emisor_data = {
            "Rfc": os.getenv('SAT_RFC'),
            "Nombre": os.getenv('SAT_NOMBRE'),
            "RegimenFiscal": os.getenv('SAT_REGIMEN_FISCAL', "601")
        }
        # Validate required fields
        if not all([emisor_data['Rfc'], emisor_data['Nombre'], emisor_data['RegimenFiscal']]):
            raise ValueError("Missing required emisor data in environment variables")
        return emisor_data

    def _prepare_receptor(self, is_public=False):
        if is_public:
            return {
                "Rfc": "XAXX010101000",
                "Nombre": "PUBLICO EN GENERAL",
                "UsoCFDI": "S01",  # Sin efectos fiscales
                "RegimenFiscalReceptor": "616",  # Sin obligaciones fiscales
                "DomicilioFiscalReceptor": os.getenv('SAT_CP', '00000')
            }
        else:
            receptor_data = {
                "Rfc": os.getenv('RECEPTOR_RFC'),
                "Nombre": os.getenv('RECEPTOR_NOMBRE'),
                "UsoCFDI": "G03",  # Gastos en general
                "RegimenFiscalReceptor": os.getenv('RECEPTOR_REGIMEN', "601"),
                "DomicilioFiscalReceptor": os.getenv('RECEPTOR_CP', '00000')
            }
            # Validate required fields
            if not all([receptor_data['Rfc'], receptor_data['Nombre']]):
                raise ValueError("Missing required receptor data in environment variables")
            return receptor_data

    def _prepare_conceptos(self, sales):
        """Prepare conceptos for CFDI"""
        total_amount = sum(sale.total_amount for sale in sales)
        return [{
            "ClaveProdServ": "01010101",  # Servicios de facturación
            "Cantidad": 1,
            "ClaveUnidad": "ACT",  # Actividad
            "Descripcion": "Venta al público en general",
            "ValorUnitario": f"{total_amount:.2f}",
            "Importe": f"{total_amount:.2f}",
            "ObjetoImp": "02",  # Sí objeto de impuesto
            "Impuestos": {
                "Traslados": [{
                    "Base": f"{total_amount:.2f}",
                    "Impuesto": "002",  # IVA
                    "TipoFactor": "Tasa",
                    "TasaOCuota": "0.160000",
                    "Importe": f"{total_amount * 0.16:.2f}"
                }]
            }
        }]

    def _call_sw_sapien_api(self, comprobante):
        """Call SW Sapien API to stamp CFDI"""
        try:
            if self.test_mode:
                # Simulate API response in test mode
                test_uuid = datetime.now().strftime('TEST-UUID-%Y%m%d-%H%M%S')
                return {
                    'uuid': test_uuid,
                    'xml': json.dumps(comprobante, indent=2)
                }
            
            response = requests.post(
                f"{self.url}/v4/cfdi33/stamp",
                headers=self.headers,
                json={"data": comprobante}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'uuid': data['data']['uuid'],
                        'xml': data['data']['cfdi']
                    }
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
                "LugarExpedicion": os.getenv('SAT_CP', '00000'),
                "Emisor": self._prepare_emisor(),
                "Receptor": self._prepare_receptor(True),
                "Conceptos": self._prepare_conceptos([sale])
            }
            
            result = self._call_sw_sapien_api(comprobante)
            
            # Create invoice record
            invoice = Invoice(
                sale_id=sale.id,
                cfdi_uuid=result['uuid'],
                xml_content=result['xml']
            )
            db.session.add(invoice)
            sale.is_invoiced = True
            db.session.commit()
            
            return result
            
        except Exception as e:
            raise Exception(f"Error generating CFDI: {str(e)}")

    def generate_global_cfdi(self, sales, date):
        """Generate global CFDI for multiple sales"""
        try:
            if not sales:
                raise ValueError("No sales provided")
                
            comprobante = {
                "Version": "4.0",
                "Serie": "G",
                "Folio": str(datetime.now().strftime("%Y%m%d%H%M%S")),
                "Fecha": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
                "FormaPago": "01",  # Efectivo
                "SubTotal": f"{sum(sale.total_amount for sale in sales):.2f}",
                "Moneda": "MXN",
                "Total": f"{sum(sale.total_amount * 1.16 for sale in sales):.2f}",  # Including IVA
                "TipoDeComprobante": "I",  # Ingreso
                "Exportacion": "01",  # No aplica
                "MetodoPago": "PUE",  # Pago en una sola exhibición
                "LugarExpedicion": os.getenv('SAT_CP', '00000'),
                "Emisor": self._prepare_emisor(),
                "Receptor": self._prepare_receptor(True),
                "Conceptos": self._prepare_conceptos(sales)
            }
            
            result = self._call_sw_sapien_api(comprobante)
            
            # Create global invoice record
            global_invoice = GlobalInvoice(
                date=date,
                total_amount=sum(sale.total_amount for sale in sales),
                tax_amount=sum(sale.total_amount * 0.16 for sale in sales),
                cfdi_uuid=result['uuid'],
                xml_content=result['xml']
            )
            
            # Mark all sales as invoiced
            for sale in sales:
                sale.is_invoiced = True
                sale.global_invoice = global_invoice
            
            db.session.add(global_invoice)
            db.session.commit()
            
            return result
            
        except Exception as e:
            raise Exception(f"Error generating Global CFDI: {str(e)}")

# Create singleton instances for different modes
cfdi_generator = CFDIGenerator(test_mode=True)  # For testing
cfdi_generator_prod = CFDIGenerator(test_mode=False)  # For production
