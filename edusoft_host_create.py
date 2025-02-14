from flask import Flask, request, render_template, redirect, url_for, flash
import os
import pandas as pd
import json
import requests
import unicodedata

# Configuración de Flask
app = Flask(__name__)
app.secret_key = "secret_key"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Zabbix API URL y credenciales
url = "http://10.177.255.28/zabbix/api_jsonrpc.php"
username = "Monitoreo"
password = "MonitoreS1mpl3##"

# Función para iniciar sesión en Zabbix
def login_zabbix(url, username, password):
    data = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {"username": username, "password": password},
        "id": 1,
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_json = response.json()

    if "result" in response_json and "error" not in response_json:
        return response_json["result"]
    else:
        raise Exception(f"Error al iniciar sesión: {response_json}")

# Función para crear conexión en Zabbix (Estructura JSON)
def create_host(url, auth_token, hostname, hostip, mac_add, groupids, contact, address, lat, lon, notes):
    data = {
        "jsonrpc": "2.0",
        "method": "host.create",
        "params": {
            "host": hostname,
            "visible": 1,
            "groups": [{"groupid": groupid} for groupid in groupids],
            "templates": [{"templateid": "10566"}],
            "interfaces": [
                {"type": 1, "main": 1, "useip": 1, "ip": hostip, "dns": "", "port": "10050"}
            ],
            "inventory_mode": 0,
            "inventory": {
                "macaddress_a": mac_add,
                "contact": contact,
                "location": address,
                "location_lat": lat,
                "location_lon": lon,
                "notes": "NAP: " + notes,
            },
        },
        "auth": auth_token,
        "id": 2,
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_json = response.json()

    if "error" in response_json:
        raise Exception(f"Error al crear el host: {response_json['error']}")
    else:
        return f"Host creado exitosamente. Host ID: {response_json['result']['hostids'][0]}"

# Función para eliminar acentos y caracteres no reconocidos por Zabbix
def quitar_acentos(cadena):
    if not isinstance(cadena, str):
        return cadena
    cadena = unicodedata.normalize("NFKD", cadena)
    return "".join(c for c in cadena if not unicodedata.combining(c)).replace("ñ", "n").replace("Ñ", "N")

# Función para extraer los grupos de hosts creados en Zabbix con sus respectivos IDs
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

# Función para mapear los grupos de la conexión cliente con los IDs registrados en Zabbix
def obtener_ids(localidad, olt, feeder, group_ids_dict):
    
    group_loc = {
        "Los teques": "Clientes FTTH POC (Los Teques)",
        "Maracay": "Clientes FTTH POC (Maracay)",
        "Valencia": "Clientes FTTH POC (Valencia)",
        "Barquisimeto": "Clientes FTTH POC (Barquisimeto)",
        "Caracas": "Clientes FTTH POC (Caracas)"
    }

    ids = ["35", "34"]

    if group_loc.get(localidad) in group_ids_dict:
        ids.append(str(group_ids_dict[group_loc.get(localidad)]))
    else:
        raise ValueError(f"Localidad: '{group_loc.get(localidad)}' no definido en Zabbix")

    if olt in group_ids_dict:
        ids.append(str(group_ids_dict[olt]))
    else:
        raise ValueError(f"OLT: '{olt}' no definida en Zabbix")

    if feeder not in ["No aplica", "N/A"]:
        if feeder in group_ids_dict:
            ids.append(str(group_ids_dict[feeder]))
        else:
            raise ValueError(f"Feeder '{feeder}' no encontrado en group_ids_dict")

    ids.append("90")
    return ids

# Función principal que permite extraer una lista con los resultados de la creación de las conexiones clientes en Zabbix y sus posibles errores
def process_excel(file_path):

    mapa_loc = {
        "Los teques": "LTQ OSS",
        "Maracay": "MCY OSS",
        "Valencia": "VAL OSS",
        "Barquisimeto": "BTO OSS",
        "Caracas": "CCS OSS",
    }

    columns = [
        "Nombre", "Customer", "Localidad", "OLT", "Feeder", 
        "NAP", "ONT/ONU", "Dirección IP", "MAC address", "Ubicación de la caja NAP (Coordenadas)", 
        "Dirección", "Numero de telefono"
    ]
    df = pd.read_excel(file_path, usecols=columns, dtype={"Numero de telefono": str})
    df = df.fillna("N/A").astype(str)

    df["Nombre"] = df["Nombre"].apply(quitar_acentos)

    df["Nombre"] = df["Nombre"].str.strip()
    df["Customer"] = df["Customer"].str.strip()
    df["ONT/ONU"] = df["ONT/ONU"].str.strip()
    df["hostname"] = df["Nombre"] + " " + df["ONT/ONU"] + " ID"     + df["Customer"] + " " + df["Localidad"].map(mapa_loc)
    client_data_dict = df.to_dict(orient="records")

    try:
        auth_token = login_zabbix(url, username, password)
    except Exception as e:
        return f"Error al iniciar sesión en Zabbix: {e}"
    
    host_groups = get_host_groups(url, auth_token)
    zabbix_group_ids = {group['name'].strip(): group['groupid'].strip() for group in host_groups}

    resultados = []
    for row in client_data_dict:
        try:
            hostname = row["hostname"]
            groupids = obtener_ids(row["Localidad"], row["OLT"], row["Feeder"], zabbix_group_ids)
            latitud = row["Ubicación de la caja NAP (Coordenadas)"].split(",")[0].strip()
            longitud = row["Ubicación de la caja NAP (Coordenadas)"].split(",")[1].strip()
            response = create_host(
                url, auth_token, hostname, row["Dirección IP"].strip(), row["MAC address"], groupids, 
                row["Numero de telefono"], row["Dirección"].strip(), latitud, longitud, row["NAP"]
            )
            resultados.append(response)
        except ValueError as e:
            resultados.append(f"Error en los datos suministrados: {row['hostname']}: {e}")
        except Exception as e:
            resultados.append(f"Error al crear host {row['hostname']}: {e}")

    return resultados

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No se seleccionó un archivo.")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No se seleccionó un archivo.")
            return redirect(request.url)
        if file:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(file_path)
            resultados = process_excel(file_path)
            return render_template("resultados.html", resultados=resultados)
    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=False)

