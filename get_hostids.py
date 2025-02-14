import json
import requests
import pandas as pd

# Reemplaza con tus credenciales y URL de Zabbix
url = "http://10.177.255.28/zabbix/api_jsonrpc.php"
username = "Monitoreo"
password = "MonitoreS1mpl3##"

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

def get_hosts(url, token):
    """
    Obtiene una lista de todos los hosts y sus IDs.
    """
    data = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "name"]  # Solo obtenemos el ID y el nombre del host
        },
        "auth": token,
        "id": 2
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_json = response.json()
    if "result" in response_json:
        return response_json["result"]
    else:
        raise Exception(f"Error al obtener los hosts: {response_json}")

# Iniciar sesión y obtener el token
auth_token = login_zabbix(url, username, password)

# Obtener todos los hosts
hosts = get_hosts(url, auth_token)

# Crear un DataFrame de pandas con los datos
df = pd.DataFrame(hosts, columns=["name", "hostid"])

# Exportar el DataFrame a un archivo Excel
output_file = "hosts_excel/hosts_zabbix.xlsx"
df.to_excel(output_file, index=False)

print(f"Datos exportados correctamente a {output_file}")