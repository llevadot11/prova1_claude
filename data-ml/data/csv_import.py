import requests
import pandas as pd
import io
import time

# 1. CONFIGURACIÓN DE SEGURIDAD (Obligatoria en 2026)
# Overpass ahora bloquea UAs genéricos. Personaliza el 'User-Agent'.
HEADERS = {
    'User-Agent': 'BarcelonaFrictionProject/1.0 (contact: tu_email@ejemplo.com)',
    'Accept': 'application/json, text/csv',
    'Referer': 'https://overpass-turbo.eu/'
}

def download_data(url, filename, is_json=True, method="GET", data=None):
    try:
        print(f"📥 Solicitando: {filename}...")
        if method == "POST":
            response = requests.post(url, data=data, headers=HEADERS, timeout=30)
        else:
            response = requests.get(url, headers=HEADERS, timeout=30)
            
        response.raise_for_status()
        
        if is_json:
            json_data = response.json()
            # Estructura para Open-Meteo o Overpass
            rows = json_data.get('hourly', json_data.get('elements', json_data))
            df = pd.DataFrame(rows)
        else:
            df = pd.read_csv(io.StringIO(response.text))
            
        df.to_csv(filename, index=False)
        print(f"✅ Guardado con éxito: {filename}")
        return True
    except Exception as e:
        print(f"❌ Fallo en {filename}: {e}")
        return False

# --- 1. METEO Y AIRE (Siguen funcionando igual) ---
LAT, LON = 41.3888, 2.159
download_data(f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=temperature_2m,precipitation&timezone=Europe%2FMadrid", "meteo.csv")
download_data(f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={LAT}&longitude={LON}&hourly=pm10,nitrogen_dioxide&timezone=Europe%2FMadrid", "aire.csv")

# --- 2. TRÁFICO (URL actualizada a Mayo 2026) ---
# En 2026, Open Data BCN usa este ID para el recurso de Mayo:
url_trafico_mayo = "https://opendata-ajuntament.barcelona.cat/data/dataset/trams/resource/0ed5dfa6-4071-4e0e-a6b7-4a1dc647b50b/download/2026_05_Maig_TRAMS_TRAMS.csv"
download_data(url_trafico_mayo, "trafico_mayo_2026.csv", is_json=False)

# --- 3. OVERPASS (Corregido con POST y Headers) ---
# Usamos POST para evitar el error 406 y ser más eficientes
overpass_url = "https://overpass-api.de/api/interpreter"
query_hospitals = {
    'data': '[out:json];area["name"="Barcelona"]->.a;node["amenity"="hospital"](area.a);out;'
}
time.sleep(2) # Respetar rate-limit
download_data(overpass_url, "hospitales.csv", method="POST", data=query_hospitals)

print("\n🚀 Todos los procesos intentados. Verifica tu carpeta local.")