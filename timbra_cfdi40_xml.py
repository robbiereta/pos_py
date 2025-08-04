import requests
import os
def stamp_cfdi():
    url = "http://services.sw.com.mx/cfdi33/stamp/v4"
    
    # Read the XML file in binary mode
    try:
        with open('MX-Global.xml', 'rb') as xml_file:
            files = {
                'xml': ('MX-Global.xml', xml_file, 'text/xml')
            }
            
            # Note: Don't set Content-Type header, requests will set it with the correct boundary
            headers = {
                'Authorization': 'bearer '+os.getenv('TOKEN_TEST'),
            }
            
            # Use requests.post directly and let it handle the multipart encoding
            response = requests.post(url, headers=headers, files=files)
            
            print(f"Status Code: {response.status_code}")
            print("Response:")
            print(response.text)
            
    except FileNotFoundError:
        print("Error: MX-Global.xml file not found in the current directory.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    stamp_cfdi()
