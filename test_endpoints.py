import requests
import json

# URL base de la API
BASE_URL = 'http://localhost:5003/api'

# Credenciales de prueba
USERNAME = 'user1'
PASSWORD = 'hashed_password'

# Crear una sesión para mantener las cookies
session = requests.Session()

# Función para obtener token de autenticación
def get_auth_token():
    login_data = {'username': USERNAME, 'password': PASSWORD}
    response = session.post(f'{BASE_URL}/login', json=login_data)
    if response.status_code == 302 or response.status_code == 200:
        print('Login exitoso')
        return True
    else:
        print('Error en login:', response.status_code, response.text)
        return False

# Función para probar el endpoint de facturación
def test_facturar_venta():
    if not get_auth_token():
        return
        
    # Primero crear una venta para obtener un ID
    venta_response = session.post(f'{BASE_URL}/sales', json={'nota_venta': 'test_factura', 'client_id': '12345', 'items': [{'product_id': 'prod1', 'quantity': 2, 'price': 100}, {'product_id': 'prod2', 'quantity': 1, 'price': 50}]})
    try:
        venta_json = venta_response.json()
        if venta_response.status_code == 201 and '_id' in venta_json:
            nota_venta_id = venta_json['_id']
            print(f'Venta creada para facturación con ID: {nota_venta_id}')
        else:
            print(f'Error al crear venta para facturación: {venta_response.status_code}')
            return
    except requests.exceptions.JSONDecodeError:
        print(f'Error al crear venta para facturación, respuesta no JSON: {venta_response.status_code} {venta_response.text}')
        return
        
    venta_data = {
        'nota_venta': nota_venta_id,
        'client_id': '12345',
        'items': [
            {'product_id': 'prod1', 'quantity': 2, 'price': 100},
            {'product_id': 'prod2', 'quantity': 1, 'price': 50}
        ]
    }
    response = session.post(f'{BASE_URL}/facturar_venta', json=venta_data)
    try:
        response_json = response.json()
        print('Facturar venta:', response.status_code, response_json)
    except requests.exceptions.JSONDecodeError:
        print('Facturar venta:', response.status_code, 'Respuesta no JSON:', response.text)

# Función para probar otros endpoints
def test_other_endpoints():
    if not get_auth_token():
        return
        
    # Probar obtener cortes
    response = session.get(f'{BASE_URL}/cortes')
    try:
        response_json = response.json()
        print('Obtener cortes:', response.status_code, response_json)
    except requests.exceptions.JSONDecodeError:
        print('Obtener cortes:', response.status_code, 'Respuesta no JSON:', response.text)

    # Probar lista de usuarios (solo para issuer)
    response = session.get(f'{BASE_URL}/users')
    try:
        response_json = response.json()
        print('Lista de usuarios:', response.status_code, response_json)
    except requests.exceptions.JSONDecodeError:
        print('Lista de usuarios:', response.status_code, 'Respuesta no JSON:', response.text)

def crud_ventas():
    if not get_auth_token():
        return
        
    # Probar CRUD de ventas
    response = session.post(f'{BASE_URL}/sales', json={'nota_venta': 'test123', 'client_id': '12345', 'items': [{'product_id': 'prod1', 'quantity': 2, 'price': 100}, {'product_id': 'prod2', 'quantity': 1, 'price': 50}]})
    try:
        response_json = response.json()
        print('Crear venta:', response.status_code, response_json)
    except requests.exceptions.JSONDecodeError:
        if response.status_code==201:print("venta creada")
        else: print("venta no creada")
    
    # Obtener una venta por ID  
    response = session.get(f'{BASE_URL}/sales/{response_json["_id"]}')
    try:
        response_json = response.json()
        if response.status_code==200:print("venta obtenida")
        else: print("venta no obtenida")
        sale_id = response_json["_id"]  # Guardamos el ID para usarlo después
    except requests.exceptions.JSONDecodeError:
        print('Obtener venta por ID:', response.status_code, 'Respuesta no JSON:', response.text)
        sale_id = None

    # Actualizar una venta
    if sale_id:
        response = session.put(f'{BASE_URL}/sales/{sale_id}', json={'nota_venta': 'test123', 'client_id': '12345', 'items': [{'product_id': 'prod1', 'quantity': 2, 'price': 100}, {'product_id': 'prod2', 'quantity': 1, 'price': 50}]})
        try:
            response_json = response.json()
            if response.status_code==200:print("venta actualizada")
            else: print("venta no actualizada")
        except requests.exceptions.JSONDecodeError:
            print('Actualizar venta:', response.status_code, 'Respuesta no JSON:', response.text)

    # Eliminar una venta
    if sale_id:
        response = session.delete(f'{BASE_URL}/sales/{sale_id}')
        try:
            response_json = response.json()
            if response.status_code==200:print("venta eliminada")
            else: print("venta no eliminada")
        except requests.exceptions.JSONDecodeError:
            print('Eliminar venta:', response.status_code, 'Respuesta no JSON:', response.text)
    else:
        print("No se pudo obtener el ID de la venta para realizar más operaciones.")
if __name__ == '__main__':
    print('Probando endpoints de la API...')
    test_facturar_venta()

    print('Pruebas completadas.')