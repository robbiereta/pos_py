import json
import re

def fix_xml_quotes(xml_str):
    # This pattern matches attribute values in the XML that are not properly escaped
    pattern = r'(\w+)="([^"]*)"'
    
    # Replace all attribute values to be properly escaped
    def replace_quotes(match):
        key = match.group(1)
        value = match.group(2)
        # Escape any double quotes in the value
        value = value.replace('"', '\\"')
        return f'{key}=\"{value}\"'
    
    # Apply the replacement to all attributes
    fixed_xml = re.sub(pattern, replace_quotes, xml_str)
    return fixed_xml

def fix_json_file(filepath):
    # Read the JSON file
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Fix the XML in data2
    if 'data2' in data:
        data['data2'] = fix_xml_quotes(data['data2'])
    
    # Write the fixed JSON back to the file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    fix_json_file('a.json')
