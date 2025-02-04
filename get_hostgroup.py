import json
import requests

# Reemplaza con tus credenciales y URL de Zabbix
url = "http://10.177.255.28/zabbix/api_jsonrpc.php"
username = "Monitoreo"
password = "MonitoreS1mpl3##"
token = "6e788c8acbfd0620c14aba8457ec1736aa44675098d684b8d9536666309b5b2a"

def login_zabbix(url, username, password):
    """
    Inicia sesión en la API de Zabbix y devuelve el token de autenticación.
    """
    data = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": username,
            "password": password
        },
        "id": 1
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_json = response.json()
    if "result" in response_json and "error" not in response_json:
        return response_json["result"]
    else:
        raise Exception(f"Error al iniciar sesión: {response_json}")

def get_host_groups(url, token):
    """
    Obtiene una lista de todos los grupos de hosts y sus IDs.
    """
    data = {
        "jsonrpc": "2.0",
        "method": "hostgroup.get",
        "params": {},
        "auth": token,
        "id": 2
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_json = response.json()
    if "result" in response_json:
        return response_json["result"]
    else:
        raise Exception(f"Error al obtener los grupos de hosts: {response_json}")

# Iniciar sesión y obtener el token
auth_token = login_zabbix(url, username, password)

# Obtener todos los grupos de hosts
host_groups = get_host_groups(url, auth_token)

# Imprimir los IDs y nombres de los grupos
for group in host_groups:
    print(f"ID: {group['groupid']}, Nombre: {group['name']}")