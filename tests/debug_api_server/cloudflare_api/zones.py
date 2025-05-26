"""
Módulo que maneja los endpoints relacionados con zonas DNS de Cloudflare.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timezone

# Crear un Blueprint para las rutas de zonas
zones_bp = Blueprint('zones', __name__)

import os
import json

# Ruta absoluta al archivo de datos compartidos
SHARED_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'debug_shared_data.json'))

def load_mock_zones():
    print(f"[MOCK] Cargando zonas desde: {SHARED_DATA_PATH}")
    if os.path.exists(SHARED_DATA_PATH):
        try:
            with open(SHARED_DATA_PATH, 'r') as f:
                data = json.load(f)
            print(f"[MOCK] Dominios encontrados en cloudflare_domains: {data.get('cloudflare_domains', [])}")
            zones = []
            for idx, domain in enumerate(data.get("cloudflare_domains", [])):
                zones.append({
                    "id": f"mock_zone_id_{idx+1}",
                    "name": domain,
                    "status": "active",
                    "created_on": "2025-01-01T00:00:00Z",
                    "modified_on": "2025-01-01T00:00:00Z"
                })
            print(f"[MOCK] Zonas cargadas: {[z['name'] for z in zones]}")
            return zones
        except Exception as e:
            print(f"[MOCK][ERROR] Error al leer debug_shared_data.json: {e}")
            return []
    else:
        print(f"[MOCK][ERROR] Archivo no encontrado: {SHARED_DATA_PATH}")
    return []

MOCK_ZONES = load_mock_zones()


@zones_bp.route('/zones', methods=['GET'])
def list_zones():
    print(f"[DEBUG] GET /zones - Query: {request.args}")
    """
    Lista las zonas DNS disponibles.
    
    Query Parameters:
        name (str, opcional): Filtra las zonas por nombre.
        status (str, opcional): Filtra las zonas por estado (ej. 'active').
        
    Returns:
        JSON: Lista de zonas que coinciden con los filtros.
    """
    # Verificar autenticación
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({
            "success": False, 
            "errors": [{"code": 6003, "message": "Invalid request headers"}],
            "messages": [{"code": 6003, "message": "Invalid request headers"}],
            "result": []
        }), 403
    
    # Validar token (solo verificación básica)
    token = auth_header.split(' ')[1]
    if not token or len(token) < 10:  # Validación básica del token
        return jsonify({
            "success": False,
            "errors": [{"code": 6003, "message": "Invalid request headers"}],
            "messages": [{"code": 6003, "message": "Invalid request headers"}],
            "result": []
        }), 403
    
    # Obtener parámetros de consulta
    zone_name = request.args.get('name')
    status = request.args.get('status', 'active')
    
    # Filtrar zonas según los parámetros
    filtered_zones = []
    for zone in MOCK_ZONES:
        # Aplicar filtros
        if zone_name and zone["name"] != zone_name:
            continue
            
        if status and zone.get("status") != status:
            continue
            
        # Construir respuesta con el formato de la API real
        zone_data = {
            "id": zone["id"],
            "name": zone["name"],
            "status": zone.get("status", "active"),
            "paused": False,
            "type": "full",
            "development_mode": 0,
            "name_servers": [
                f"ns1.{zone['name']}",
                f"ns2.{zone['name']}"
            ],
            "original_name_servers": None,
            "original_registrar": None,
            "original_dnshost": None,
            "modified_on": zone.get("modified_on", datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')),
            "created_on": zone.get("created_on", datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')),
            "activated_on": zone.get("activated_on", datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')),
            "meta": {
                "step": 2,
                "custom_certificate_quota": 0,
                "page_rule_quota": 3,
                "phishing_detected": False
            },
            "owner": {
                "id": "7ae3782b91d2827bcd865d3cd9d7182c",
                "type": "user",
                "email": "usuario@ejemplo.com"
            },
            "account": {
                "id": "9fff3513fb250e4890d55655f987effd",
                "name": f"{zone['name']}'s Account"
            },
            "tenant": {
                "id": None,
                "name": None
            },
            "tenant_unit": {
                "id": None
            },
            "permissions": ["#dns_records:read", "#zone:read"],
            "plan": {
                "id": "0feeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "name": "Free Website",
                "price": 0,
                "currency": "USD",
                "frequency": "",
                "legacy_id": "free",
                "is_subscribed": True,
                "can_subscribe": False
            }
        }
        filtered_zones.append(zone_data)
    
    # Construir respuesta
    response = {
        "result": filtered_zones,
        "success": True,
        "errors": [],
        "messages": []
    }
    
    # Agregar información de paginación si hay resultados
    if filtered_zones:
        response["result_info"] = {
            "page": 1,
            "per_page": 20,
            "count": len(filtered_zones),
            "total_count": len(filtered_zones),
            "total_pages": 1
        }
    
    return jsonify(response)


@zones_bp.route('/zones/<zone_id>', methods=['GET'])
def get_zone(zone_id):
    print(f"[DEBUG] GET /zones/{zone_id}")
    """
    Obtiene los detalles de una zona específica.
    
    Args:
        zone_id (str): ID de la zona a consultar.
        
    Returns:
        JSON: Detalles de la zona o mensaje de error si no se encuentra.
    """
    # Verificar autenticación
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({
            "success": False, 
            "errors": [{"code": 6003, "message": "Invalid request headers"}],
            "messages": [{"code": 6003, "message": "Invalid request headers"}],
            "result": None
        }), 403
    
    # Validar token (solo verificación básica)
    token = auth_header.split(' ')[1]
    if not token or len(token) < 10:  # Validación básica del token
        return jsonify({
            "success": False,
            "errors": [{"code": 6003, "message": "Invalid request headers"}],
            "messages": [{"code": 6003, "message": "Invalid request headers"}],
            "result": None
        }), 403
    
    # Validar formato del ID de zona
    if not zone_id or len(zone_id) != 32 or not all(c in '0123456789abcdef' for c in zone_id):
        return jsonify({
            "success": False,
            "errors": [{"code": 9109, "message": "Invalid zone identifier"}],
            "messages": [],
            "result": None
        }), 400
    
    # Buscar la zona
    zone = next((z for z in MOCK_ZONES if z["id"] == zone_id), None)
    
    if not zone:
        return jsonify({
            "success": False,
            "errors": [{"code": 9109, "message": "Invalid zone identifier"}],
            "messages": [],
            "result": None
        }), 400
    
    # Construir respuesta con el formato de la API real
    zone_data = {
        "id": zone["id"],
        "name": zone["name"],
        "status": zone.get("status", "active"),
        "paused": False,
        "type": "full",
        "development_mode": 0,
        "name_servers": [
            f"ns1.cloudflare.com",
            f"ns2.cloudflare.com"
        ],
        "original_name_servers": None,
        "original_registrar": None,
        "original_dnshost": None,
        "modified_on": zone.get("modified_on", datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')),
        "created_on": zone.get("created_on", datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')),
        "activated_on": zone.get("activated_on", datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')),
        "meta": {
            "step": 2,
            "custom_certificate_quota": 0,
            "page_rule_quota": 3,
            "phishing_detected": False
        },
        "owner": {
            "id": "7ae3782b91d2827bcd865d3cd9d7182c",
            "type": "user",
            "email": "usuario@ejemplo.com"
        },
        "account": {
            "id": "9fff3513fb250e4890d55655f987effd",
            "name": f"{zone['name']}'s Account"
        },
        "tenant": {
            "id": None,
            "name": None
        },
        "tenant_unit": {
            "id": None
        },
        "permissions": ["#dns_records:read", "#zone:read"],
        "plan": {
            "id": "0feeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            "name": "Free Website",
            "price": 0,
            "currency": "USD",
            "frequency": "",
            "legacy_id": "free",
            "is_subscribed": True,
            "can_subscribe": False
        }
    }
    
    return jsonify({
        "success": True,
        "errors": [],
        "messages": [],
        "result": zone_data
    })
