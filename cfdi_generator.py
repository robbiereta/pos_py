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
        """Prepare conceptos for CFDI, each sale is a separate concepto"""
        conceptos = []
        for sale in sales:
            # Calcular montos
            total = sale.total_amount
            tax_rate = 0.16
            subtotal = total / (1 + tax_rate)
            tax_amount = total - subtotal
            
            # Obtener productos de la venta
            try:
                productos = sale.products
                if isinstance(productos, list):
                    descripcion = ", ".join([f"{p.get('quantity', 1)}x {p.get('name', 'Producto')}" for p in productos])
                elif isinstance(productos, dict):
                    descripcion = ", ".join([f"{qty}x {name}" for name, qty in productos.items()])
                else:
                    descripcion = "Venta general"
            except Exception as e:
                print(f"Error al procesar productos de venta {sale.id}: {str(e)}")
                descripcion = f"Venta general #{sale.id}"
            
            concepto = {
                "ClaveProdServ": "01010101",  # No existe en el catálogo
                "Cantidad": 1,
                "ClaveUnidad": "ACT",  # Actividad
                "Descripcion": descripcion,
                "ValorUnitario": f"{subtotal:.2f}",
                "Importe": f"{subtotal:.2f}",
                "ObjetoImp": "02",  # Sí objeto de impuesto
                "Impuestos": {
                    "Traslados": [{
                        "Base": f"{subtotal:.2f}",
                        "Impuesto": "002",  # IVA
                        "TipoFactor": "Tasa",
                        "TasaOCuota": "0.160000",
                        "Importe": f"{tax_amount:.2f}"
                    }]
                }
            }
            conceptos.append(concepto)
        
        return conceptos

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
        
            # Log request data
            print("\nEnviando comprobante:")
            print(json.dumps(comprobante, indent=2))
        
            response = requests.post(
                f"{self.url}/v3/cfdi33/issue/json/v4",
                headers=self.headers,
                json=comprobante
            )
        
            # Log response
            print("\nRespuesta del servidor:")
            print(f"Status: {response.status_code}")
            try:
                print(json.dumps(response.json(), indent=2))
            except:
                print(response.text)
        
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
        """
        Generate a global CFDI for multiple sales
        """
        try:
            # Calcular totales
            total_amount = sum(sale.total_amount for sale in sales)
            # El IVA ya está incluido en el total, así que lo extraemos (16%)
            subtotal = total_amount / 1.16
            tax_amount = total_amount - subtotal

            # Preparar el comprobante
            comprobante = {
                "Version": "4.0",
                "Serie": "G",  # G para facturas globales
                "Fecha": date.strftime("%Y-%m-%dT%H:%M:%S"),
                "FormaPago": "01",  # 01 - Efectivo
                "SubTotal": f"{subtotal:.2f}",
                "Moneda": "MXN",
                "Total": f"{total_amount:.2f}",
                "TipoDeComprobante": "I",  # I - Ingreso
                "Exportacion": "01",  # 01 - No aplica
                "MetodoPago": "PUE",  # PUE - Pago en una sola exhibición
                "LugarExpedicion": os.getenv('SAT_CP', '00000'),
                "Emisor": self._prepare_emisor(),
                "Receptor": self._prepare_receptor(True),
                "Conceptos": [{
                    "ClaveProdServ": "01010101",  # No existe en el catálogo
                    "Cantidad": "1",
                    "ClaveUnidad": "ACT",  # Actividad
                    "Descripcion": "Venta",
                    "ValorUnitario": f"{subtotal:.2f}",
                    "Importe": f"{subtotal:.2f}",
                    "ObjetoImp": "02",  # 02 - Sí objeto de impuesto
                    "Impuestos": {
                        "Traslados": [{
                            "Base": f"{subtotal:.2f}",
                            "Impuesto": "002",  # 002 - IVA
                            "TipoFactor": "Tasa",
                            "TasaOCuota": "0.160000",
                            "Importe": f"{tax_amount:.2f}"
                        }]
                    }
                }],
                "Impuestos": {
                    "TotalImpuestosTrasladados": f"{tax_amount:.2f}",
                    "Traslados": [{
                        "Base": f"{subtotal:.2f}",
                        "Impuesto": "002",  # 002 - IVA
                        "TipoFactor": "Tasa",
                        "TasaOCuota": "0.160000",
                        "Importe": f"{tax_amount:.2f}"
                    }]
                }
            }

            # Timbrar el CFDI
            response = self._call_sw_sapien_api(comprobante)
            return response

        except Exception as e:
            raise Exception(f"Error generating Global CFDI: {str(e)}")

# Create singleton instances for different modes
cfdi_generator = CFDIGenerator(test_mode=True)  # For testing
cfdi_generator_prod = CFDIGenerator(test_mode=False)  # For production
