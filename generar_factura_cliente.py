from cfdi_generator import CFDIGenerator
import os
from flask import Flask
from routes import create_app
from datetime import datetime

def generar_factura_cliente(nota_venta):
    app = create_app()
    
    with app.app_context():
        try:
            # Obtener venta específica por ID
            sale = app.db.sales.find_one({"_id": nota_venta})
            
            if not sale:
                print(f"No se encontró la venta con ID {nota_venta}.")
                return
            
            print(f"\nGenerando factura para la nota de venta {nota_venta}...")
            
            # Obtener información del cliente
            client_id = sale.get('client_id')
            client = app.db.clients.find_one({"_id": client_id}) if client_id else None
            
            if not client:
                print("No se encontró información del cliente. No se puede generar factura.")
                return
            
            # Calcular totales
            total_amount = sale.get('total_amount', 0)
            # El IVA ya está incluido en el total, así que lo extraemos (16%)
            subtotal = total_amount / 1.16
            tax_amount = total_amount - subtotal
            
            # Obtener fecha actual
            fecha_emision = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            
            # Preparar conceptos (productos) de la venta
            conceptos = []
            for item in sale.get('items', []):
                concepto = {
                    'ClaveProdServ': item.get('product_code', '01010101'),
                    'Cantidad': item.get('quantity', 1),
                    'ClaveUnidad': item.get('unit_code', 'H87'),
                    'Unidad': item.get('unit', 'Pieza'),
                    'Descripcion': item.get('description', 'Producto'),
                    'ValorUnitario': item.get('price', 0),
                    'Importe': item.get('total', 0),
                    'Descuento': item.get('discount', 0),
                    'ObjetoImp': '02',  # Objeto de impuesto
                    'Impuestos': {
                        'Traslados': [{
                            'Base': item.get('total', 0) / 1.16,
                            'Impuesto': '002',  # IVA
                            'TipoFactor': 'Tasa',
                            'TasaOCuota': '0.160000',
                            'Importe': item.get('total', 0) - (item.get('total', 0) / 1.16)
                        }]
                    }
                }
                conceptos.append(concepto)
            
            # Preparar datos para el CFDI
            cfdi_data = {
                'Serie': 'A',
                'Folio': str(nota_venta)[-6:],  # Últimos 6 dígitos del ID de venta
                'Fecha': fecha_emision,
                'FormaPago': sale.get('payment_method', '01'),  # 01 - Efectivo
                'MetodoPago': 'PUE',  # Pago en una sola exhibición
                'LugarExpedicion': '67100',  # Código postal
                'Receptor': {
                    'Rfc': client.get('rfc', 'XAXX010101000'),
                    'Nombre': client.get('name', 'PUBLICO EN GENERAL'),
                    'UsoCFDI': client.get('uso_cfdi', 'G03'),  # Gastos en general
                    'RegimenFiscalReceptor': client.get('regimen_fiscal', '616'),  # Sin obligaciones fiscales
                    'DomicilioFiscalReceptor': client.get('codigo_postal', '67100')
                },
                'Conceptos': conceptos,
                'Impuestos': {
                    'TotalImpuestosTrasladados': tax_amount,
                    'Traslados': [{
                        'Impuesto': '002',
                        'TipoFactor': 'Tasa',
                        'TasaOCuota': '0.160000',
                        'Importe': tax_amount
                    }]
                },
                'SubTotal': round(subtotal, 2),
                'Total': round(total_amount, 2)
            }
            
            # Generar CFDI
            generator = CFDIGenerator()
            xml_path = generator.generate_cfdi(cfdi_data, f"factura_{nota_venta}.xml")
            
            if xml_path:
                print(f"Factura generada exitosamente: {xml_path}")
                # Actualizar estado de la venta
                app.db.sales.update_one(
                    {"_id": nota_venta},
                    {"$set": {"facturada": True, "fecha_factura": datetime.now()}}
                )
            else:
                print("Error al generar la factura.")
                
        except Exception as e:
            print(f"Error al generar factura: {str(e)}")

if __name__ == "__main__":
    generar_factura_cliente()
