from cfdi_generator import cfdi_generator
from datetime import datetime, timedelta
import os

def descargar_xmls():
    # Crear directorio para XMLs si no existe
    xml_dir = "xmls"
    if not os.path.exists(xml_dir):
        os.makedirs(xml_dir)

    # Obtener CFDIs del último mes
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"\nObteniendo CFDIs del {start_date.date()} al {end_date.date()}...")
    cfdis = cfdi_generator.list_cfdis(start_date=start_date, end_date=end_date)
    
    if not cfdis:
        print("No se encontraron CFDIs en este periodo.")
        return
        
    print(f"\nSe encontraron {len(cfdis)} CFDIs.")
    print("Descargando XMLs...")
    
    for i, cfdi in enumerate(cfdis, 1):
        uuid = cfdi.get('uuid')
        if not uuid:
            continue
            
        print(f"\nDescargando XML {i}/{len(cfdis)}")
        print(f"UUID: {uuid}")
        
        try:
            xml_content = cfdi_generator.download_xml_from_pac(uuid)
            if xml_content:
                # Guardar XML
                filename = f"{xml_dir}/cfdi_{uuid}.xml"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(xml_content)
                print(f"XML guardado como: {filename}")
            else:
                print(f"No se pudo obtener el XML para el UUID: {uuid}")
        except Exception as e:
            print(f"Error al descargar XML {uuid}: {str(e)}")
    
    print("\n¡Proceso completado!")
    print(f"Los XMLs se han guardado en el directorio: {xml_dir}")

if __name__ == "__main__":
    descargar_xmls()
