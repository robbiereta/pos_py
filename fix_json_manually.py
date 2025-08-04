import json

def fix_json_file(input_file, output_file):
    # Read the file as plain text
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the start and end of the data2 field
    start_marker = '"data2": "<?xml version="
    start_idx = content.find(start_marker)
    
    if start_idx == -1:
        print("Could not find data2 field in the file")
        return
    
    # The actual XML starts after the opening quote of data2
    xml_start = content.find('<?xml', start_idx)
    if xml_start == -1:
        print("Could not find XML start in data2")
        return
    
    # Find the end of the XML (look for the closing cfdi:Comprobante tag)
    xml_end = content.find('</cfdi:Comprobante>', xml_start)
    if xml_end == -1:
        print("Could not find XML end in data2")
        return
    
    xml_end += len('</cfdi:Comprobante>')
    
    # Extract the XML
    xml_content = content[xml_start:xml_end]
    
    # Escape the XML content for JSON
    escaped_xml = xml_content.replace('"', '\\"').replace('\n', '\\n')
    
    # Reconstruct the JSON with properly escaped XML
    fixed_content = (
        content[:start_idx] + 
        '"data2": "' + escaped_xml + '"' +
        content[content.find('"', xml_end + 1) + 1:]
    )
    
    # Write the fixed content to a new file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"Fixed JSON written to {output_file}")

if __name__ == "__main__":
    fix_json_file('a.json', 'fixed_a.json')
