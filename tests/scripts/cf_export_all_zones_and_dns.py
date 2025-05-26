"""
Script minimalista para exportar (guardar en archivos JSON) todas las zonas y todos los registros DNS de cada zona de una cuenta Cloudflare.
- Requiere: requests
- Uso: python cf_export_all_zones_and_dns.py <API_TOKEN>
- Guarda: zones.json y dns_records_<zone_id>.json en el mismo directorio del script.
"""
import sys
import requests
import json
import time
import random
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuración de pausas
DEFAULT_DELAY = 2.0  # Segundos de espera entre peticiones
RANDOM_DELAY_RANGE = (1.0, 3.0)  # Rango aleatorio para variar el delay
RATE_LIMIT_WINDOW = 300  # Ventana de tiempo para el rate limit (5 minutos)
MAX_REQUESTS_PER_WINDOW = 1200  # Límite de peticiones por ventana (1200/5min = 4 req/seg)

# Variables globales para el control de rate limiting
request_timestamps = []
last_request_time = 0

if len(sys.argv) < 2:
    print("Uso: python cf_export_all_zones_and_dns.py <API_TOKEN>")
    sys.exit(1)

API_TOKEN = sys.argv[1]
BASE_URL = "https://api.cloudflare.com/client/v4"

# Configuración de reintentos
retry_strategy = Retry(
    total=5,  # Número total de reintentos
    backoff_factor=1,  # Tiempo de espera entre reintentos (segundos)
    status_forcelist=[429, 500, 502, 503, 504],  # Códigos de estado para reintentar
    allowed_methods=["GET", "POST"]  # Métodos HTTP para reintentar
)

# Configurar la sesión con reintentos
session = requests.Session()
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Headers para todos los endpoints (API Token)
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def wait_for_rate_limit():
    """Espera si es necesario para respetar los límites de la API"""
    global request_timestamps, last_request_time
    
    now = time.time()
    
    # Limpiar registros antiguos (más allá de la ventana de tiempo)
    request_timestamps = [t for t in request_timestamps if now - t < RATE_LIMIT_WINDOW]
    
    # Si hemos alcanzado el límite, esperar hasta que se libere espacio
    if len(request_timestamps) >= MAX_REQUESTS_PER_WINDOW:
        oldest_request = min(request_timestamps)
        wait_time = (oldest_request + RATE_LIMIT_WINDOW) - now
        if wait_time > 0:
            print(f"Límite de tasa alcanzado. Esperando {wait_time:.1f} segundos...")
            time.sleep(wait_time + 0.5)  # Pequeño margen adicional
    
    # Aplicar un retraso entre peticiones
    time_since_last = now - last_request_time if last_request_time > 0 else 0
    if time_since_last < DEFAULT_DELAY:
        time.sleep(DEFAULT_DELAY - time_since_last + random.uniform(*RANDOM_DELAY_RANGE))
    
    last_request_time = time.time()
    request_timestamps.append(last_request_time)

def make_request(url, method='get', **kwargs):
    """Función auxiliar para realizar peticiones HTTP con manejo de errores"""
    max_retries = 3
    backoff_factor = 1
    
    for attempt in range(max_retries):
        try:
            # Respetar los límites de la API
            wait_for_rate_limit()
            
            # Realizar la petición
            response = session.request(method, url, headers=headers, timeout=30, **kwargs)
            
            # Manejar códigos de estado
            if response.status_code == 429:  # Too Many Requests
                retry_after = int(response.headers.get('Retry-After', 30))
                print(f"Rate limit alcanzado. Esperando {retry_after} segundos...")
                time.sleep(retry_after)
                continue
                
            # Si la respuesta es exitosa, actualizar los encabezados de rate limit
            if 'X-RateLimit-Remaining' in response.headers:
                remaining = int(response.headers['X-RateLimit-Remaining'])
                if remaining < 10:  # Si quedan pocas peticiones, esperar
                    reset_time = int(response.headers.get('X-RateLimit-Reset', '1'))
                    print(f"Quedan pocas peticiones ({remaining}). Próximo reset en {reset_time}s")
            
            return response
            
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión (intento {attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                print("Número máximo de reintentos alcanzado.")
                raise
                
            # Backoff exponencial con jitter
            sleep_time = min(backoff_factor * (2 ** attempt) + random.uniform(0, 1), 60)
            print(f"Reintentando en {sleep_time:.1f} segundos...")
            time.sleep(sleep_time)

# Obtener todas las zonas
try:
    resp = make_request(f"{BASE_URL}/zones")
    if not resp.ok:
        print(f"Error al obtener zonas: {resp.text}")
        sys.exit(1)
    zonas_full = resp.json()
    zonas = zonas_full.get("result", [])
except Exception as e:
    print(f"Error crítico al obtener las zonas: {str(e)}")
    print("Verifica tu conexión a internet y la configuración de red.")
    sys.exit(1)

# Obtener timestamp actual para usar en los nombres de archivo
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

# Guardar la respuesta completa de zonas
zones_full_filename = f"{current_time}_zones_full.json"
with open(zones_full_filename, "w", encoding="utf-8") as f:
    json.dump(zonas_full, f, indent=2, ensure_ascii=False)
print(f"Guardado: {zones_full_filename} (respuesta completa - {len(zonas_full.get('result', []))} zonas)")

# Extraer la lista de zonas para procesar
zonas = zonas_full.get("result", [])

for zona in zonas:
    zone_id = zona['id']
    zone_name = zona['name']
    print(f"Exportando registros DNS de zona: {zone_name} ({zone_id}) ...")
    dns_records = []
    page = 1
    per_page = 100
    while True:
        try:
            dns_resp = make_request(
                f"{BASE_URL}/zones/{zone_id}/dns_records",
                params={"page": page, "per_page": per_page}
            )
            if not dns_resp.ok:
                print(f"  Error al obtener registros DNS: {dns_resp.text}")
                break
                
            data = dns_resp.json()
            
            # Guardar la respuesta completa de cada página
            dns_records_filename = f"{current_time}_dns_records_{zone_name}_p{page}.json"
            with open(dns_records_filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  Guardado: {dns_records_filename} ({len(data.get('result', []))} registros)")
                
            dns_records.extend(data.get("result", []))
            
            # Verificar si hay más páginas
            result_info = data.get("result_info", {})
            if not result_info or result_info.get("page", 0) >= result_info.get("total_pages", 1):
                break
                
            page += 1
            
            # El tiempo de espera ya está manejado por wait_for_rate_limit()
            pass
            
        except Exception as e:
            print(f"  Error al procesar la página {page} de registros DNS: {str(e)}")
            print(f"  Continuando con los registros obtenidos hasta ahora...")
            break
    # No guardar la versión combinada, solo mantenemos las respuestas completas por página
    print(f"  Procesados {len(dns_records)} registros DNS para {zone_name}")
print("Exportación completa.")
