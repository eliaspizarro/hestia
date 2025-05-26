# cloudflare_dns.py
# Funciones para interactuar con la API de Cloudflare
# Todos los comentarios y documentación estarán en español.

import requests
import random
import time
from typing import List, Dict, Any, Optional, Tuple
from filter_utils import filter_excluded

# Estas funciones asumen que el token y la URL base se obtienen de variables de entorno o configuración externa


def _delay_before_request():
    """
    Añade un retraso aleatorio alrededor del minimo 204ms antes de cada petición a la API.
    Esto ayuda a evitar sobrecargar los servidores de Cloudflare.
    """
    time.sleep(random.uniform(0.14, 0.31))


def find_zone_for_domain(api_base_url: str, api_token: str, domain: str) -> Optional[Dict[str, str]]:
    """
    Encuentra la zona de Cloudflare que corresponde a un dominio dado.
    Si el dominio es un registro DNS (ej: subdominio.ejemplo.com), encuentra la zona padre (ej: ejemplo.com).
    """
    _delay_before_request()
    zones = list_zones(api_base_url, api_token)
    
    # Ordenar zonas por longitud de nombre (más larga primero) para encontrar la coincidencia más específica
    zones_sorted = sorted(zones, key=lambda z: len(z['name']), reverse=True)
    
    # Buscar la zona más específica que coincida con el dominio o sea un padre del mismo
    domain_parts = domain.split('.')
    for i in range(len(domain_parts) - 1):
        possible_zone = '.'.join(domain_parts[i:])
        for zone in zones_sorted:
            if zone['name'] == possible_zone:
                return zone
    return None


def list_zones(api_base_url: str, api_token: str) -> List[Dict[str, Any]]:
    """
    Obtiene la lista de zonas (dominios) de Cloudflare.
    Devuelve una lista de diccionarios con al menos 'id' y 'name'.
    """
    _delay_before_request()
    url = f"{api_base_url}/zones"
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return [{"id": z["id"], "name": z["name"]} for z in data.get("result", [])]


def list_dns_records(api_base_url: str, api_token: str, zone_id: str, name: str = None) -> List[Dict[str, Any]]:
    """
    Obtiene los registros DNS de una zona específica de Cloudflare.
    Si se proporciona 'name', filtra los registros por ese nombre.
    """
    _delay_before_request()
    url = f"{api_base_url}/zones/{zone_id}/dns_records"
    if name:
        url += f"?name={name}"
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data.get("result", [])


def update_dns_record(api_base_url: str, api_token: str, zone_id: str, record_id: str, name: str, ip: str, ttl: int = 1, proxied: bool = False) -> Dict[str, Any]:
    """
    Actualiza el registro A de un dominio en Cloudflare con la nueva IP.
    """
    _delay_before_request()
    url = f"{api_base_url}/zones/{zone_id}/dns_records/{record_id}"
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    payload = {
        "type": "A",
        "name": name,
        "content": ip,
        "ttl": ttl,
        "proxied": proxied
    }
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
