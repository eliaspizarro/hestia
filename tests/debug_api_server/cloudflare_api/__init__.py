"""
Paquete que contiene los endpoints de la API de Cloudflare simulada.
"""

from .zones import zones_bp
from .dns_records import dns_records_bp

# Lista de blueprints que deben ser registrados
blueprints = [
    zones_bp,
    dns_records_bp
]
