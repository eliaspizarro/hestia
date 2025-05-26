# src/ip_utils.py
from typing import List, Optional
import requests
import ipaddress
from logger import get_logger

logger = get_logger(__name__)

def get_external_ip(ip_service_urls: List[str]) -> Optional[str]:
    """
    Obtiene la IP externa consultando los servicios proporcionados.
    
    Args:
        ip_service_urls: Lista de URLs de servicios para obtener la IP
        
    Returns:
        La IP como string si se pudo obtener, None en caso contrario
    """
    for service_url in ip_service_urls:
        try:
            logger.debug(f"Intentando obtener IP desde: {service_url}")
            response = requests.get(service_url, timeout=10)
            response.raise_for_status()
            
            # Intentar extraer IP de JSON o usar texto plano
            content_type = response.headers.get("content-type", "").lower()
            ip_str = response.json().get("ip", "") if "json" in content_type else response.text.strip()
            
            if ip_str and ipaddress.ip_address(ip_str):
                logger.info(f"IP externa obtenida: {ip_str} de {service_url}")
                return ip_str
                
        except (requests.RequestException, ValueError, AttributeError) as e:
            logger.debug(f"Error con {service_url}: {str(e)}")
    
    logger.debug("No se pudo obtener la IP externa de ningún servicio")
    return None
