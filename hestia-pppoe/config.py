# src/config.py
import os
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

# Importar logger sin causar inicialización circular
from logger import get_logger

# Configurar logger - lo definimos primero para que esté disponible en todas las funciones
logger = get_logger(__name__)

# Constantes
DEFAULT_CONFIG: Dict[str, Any] = {
    "CLOUDFLARE_API_BASE_URL": "https://api.cloudflare.com/client/v4",
    "IP_SERVICE_URLS": "https://api.ipify.org,https://ifconfig.me/ip",
    "LOG_LEVEL": "INFO",
    "V_LIST_USERS_PATH": "/usr/local/hestia/bin/v-list-users",
    "V_LIST_WEB_DOMAINS_PATH": "/usr/local/hestia/bin/v-list-web-domains",
    "V_UPDATE_SYS_IP_PATH": "/usr/local/hestia/bin/v-update-sys-ip",
    "CLOUDFLARE_EXCLUDED_DOMAINS": "",  # Lista vacía por defecto
}

def load_environment() -> bool:
    """
    Carga las variables de entorno desde el archivo .env si existe.
    Orden de búsqueda:
    1. Junto al código fuente (desarrollo) o ejecutable (producción)
    2. /etc/hestia-pppoe/.env como último recurso
    """
    # 1. Buscar .env local (desarrollo o producción)
    if not getattr(sys, 'frozen', False):
        dotenv_path = Path(__file__).parent / ".env"
    else:
        dotenv_path = Path(sys.executable).parent / ".env"

    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path, override=True)
        logger.info(f"Cargando configuración desde: {dotenv_path}")
        return True

    # 2. Buscar en /etc/hestia-pppoe/.env como último recurso
    etc_env_path = Path("/etc/hestia-pppoe/.env")
    if etc_env_path.exists():
        load_dotenv(dotenv_path=etc_env_path, override=True)
        logger.info(f"Cargando configuración desde: {etc_env_path}")
        return True

    logger.warning(f"No se encontró ningún archivo .env válido (intentado: {dotenv_path}, {etc_env_path})")
    return False

def get_config() -> Dict[str, Any]:
    """Obtiene la configuración del sistema."""
    config = {}
    
    try:
        # Cargar configuración desde variables de entorno con valores por defecto
        for key, default in DEFAULT_CONFIG.items():
            config[key] = os.getenv(key, default)
        
        # Procesar valores especiales
        config["CLOUDFLARE_EXCLUDED_DOMAINS"] = [
            d.strip() 
            for d in os.getenv("CLOUDFLARE_EXCLUDED_DOMAINS", "").split(",") 
            if d.strip()
        ]
        
        config["IP_SERVICE_URLS"] = [
            url.strip() 
            for url in os.getenv("IP_SERVICE_URLS", DEFAULT_CONFIG["IP_SERVICE_URLS"]).split(",") 
            if url.strip()
        ]
        
        # Asegurar que el nivel de log sea válido
        log_level = config["LOG_LEVEL"].upper()
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level not in valid_levels:
            logger.warning(f"Nivel de log inválido: {log_level}. Usando valor por defecto: {DEFAULT_CONFIG['LOG_LEVEL']}")
            log_level = DEFAULT_CONFIG['LOG_LEVEL'].upper()
        
        # Aplicar el nivel de log validado al logger global
        from logger import HestiaLogger
        HestiaLogger().set_log_level(log_level)
        logger.info(f"Nivel de log configurado a: {log_level}")
        
        return config
        
    except Exception as e:
        logger.error(f"Error al cargar la configuración: {e}")
        return DEFAULT_CONFIG.copy()

# Cargar configuración al importar el módulo
load_environment()
config = get_config()

# Validar configuración
def validate_config() -> bool:
    """Valida la configuración mínima requerida."""
    required_vars = ["CLOUDFLARE_API_TOKEN"]
    
    for var in required_vars:
        if not os.getenv(var):
            logger.critical(f"Variable de entorno requerida no configurada: {var}")
            return False
    
    if not config.get("IP_SERVICE_URLS"):
        logger.critical("No hay servicios de IP configurados")
        return False
    
    logger.debug("Configuración validada correctamente")
    return True

# Validar token de Cloudflare
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
if not CLOUDFLARE_API_TOKEN:
    logger.critical("ERROR: CLOUDFLARE_API_TOKEN no encontrado en .env")
    sys.exit(1)

# Exportar configuración como variables de módulo
CLOUDFLARE_API_BASE_URL = config["CLOUDFLARE_API_BASE_URL"]
CLOUDFLARE_EXCLUDED_DOMAINS = config["CLOUDFLARE_EXCLUDED_DOMAINS"]
LOG_LEVEL = config["LOG_LEVEL"]
IP_SERVICE_URLS = config["IP_SERVICE_URLS"]
V_LIST_USERS_PATH = config["V_LIST_USERS_PATH"]
V_LIST_WEB_DOMAINS_PATH = config["V_LIST_WEB_DOMAINS_PATH"]
V_UPDATE_SYS_IP_PATH = config["V_UPDATE_SYS_IP_PATH"]
