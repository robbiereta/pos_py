def fix_json():
    # Read the file
    with open('a.json', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the start of the second XML (after the first XML)
    first_xml_end = content.find('</cfdi:Comprobante>')
    if first_xml_end == -1:
        print("Error: Couldn't find the end of the first XML")
        return
    
    # Find the start of the second XML
    second_xml_start = content.find('<?xml', first_xml_end)
    if second_xml_start == -1:
        print("Error: Couldn't find the start of the second XML")
        return
    
    # Find the end of the second XML
    second_xml_end = content.find('</cfdi:Comprobante>', second_xml_start) + len('</cfdi:Comprobante>')
    
    # Extract the second XML
    second_xml = content[second_xml_start:second_xml_end]
    
    # Escape the XML for JSON
    escaped_xml = second_xml.replace('"', '\\"').replace('\n', '\\n')
    
    # Reconstruct the content
    fixed_content = content[:second_xml_start] + escaped_xml + content[second_xml_end:]
    
    # Write the fixed content to a new file
    with open('fixed_a.json', 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("Fixed file saved as 'fixed_a.json'")

if __name__ == "__main__":
    fix_json()
