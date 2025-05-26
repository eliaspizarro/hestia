"""
Módulo que maneja el endpoint para listar registros DNS de Cloudflare.
"""

import re
from flask import Blueprint, jsonify, request
from datetime import datetime, timezone

# Importar zonas al final para evitar dependencias circulares
from .zones import MOCK_ZONES

# Crear Blueprint para las rutas de registros DNS
dns_records_bp = Blueprint('dns_records', __name__)

import os
import json

# Ruta absoluta al archivo de datos compartidos
SHARED_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'debug_shared_data.json'))

def load_mock_dns_records():
    print(f"[MOCK] Cargando registros DNS desde: {SHARED_DATA_PATH}")
    if os.path.exists(SHARED_DATA_PATH):
        try:
            with open(SHARED_DATA_PATH, 'r') as f:
                data = json.load(f)
            cloudflare_domains = data.get("cloudflare_domains", {})
            print(f"[MOCK] Dominios encontrados en cloudflare_domains: {list(cloudflare_domains.keys())}")
            records = {}
            for idx, (domain, registros) in enumerate(cloudflare_domains.items()):
                zone_id = f"mock_zone_id_{idx+1}"
                # Solo registros tipo A
                registros_a = [
                    {
                        "id": f"mock_dns_id_{idx+1}_{i+1}",
                        "type": "A",
                        "name": reg["name"],
                        "content": reg["content"],
                        "proxied": False,
                        "ttl": 1,
                        "created_on": "2025-01-01T00:00:00Z",
                        "modified_on": "2025-01-01T00:00:00Z"
                    }
                    for i, reg in enumerate(registros)
                ]
                records[zone_id] = registros_a
            print(f"[MOCK] Registros DNS generados para zonas: {list(records.keys())}")
            return records
        except Exception as e:
            print(f"[MOCK][ERROR] Error al leer debug_shared_data.json: {e}")
            return {}
    else:
        print(f"[MOCK][ERROR] Archivo no encontrado: {SHARED_DATA_PATH}")
    return {}

MOCK_DNS_RECORDS = load_mock_dns_records()


# Datos de ejemplo para zonas (usados en las respuestas)
MOCK_ZONES = [
    {
        "id": "eee3864538734cd57fecd8eaa51a91bb",
        "name": "binarius.cl"
    }
]

def _verify_auth():
    """
    Verifica la autenticación del usuario.
    
    Returns:
        tuple: (error_response, status_code) si hay un error, (None, None) si es válido.
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return ({
            "success": False,
            "errors": [{"code": 6003, "message": "Invalid request headers"}],
            "messages": [{"code": 6003, "message": "Invalid request headers"}],
            "result": None
        }, 403)
    
    token = auth_header.split(' ')[1]
    if not token or len(token) < 10:  # Validación básica del token
        return ({
            "success": False,
            "errors": [{"code": 6003, "message": "Invalid request headers"}],
            "messages": [{"code": 6003, "message": "Invalid request headers"}],
            "result": None
        }, 403)
    
    return (None, None)

@dns_records_bp.route('/zones/<zone_id>/dns_records', methods=['GET'])
def list_dns_records(zone_id):
    print(f"[DEBUG] GET /zones/{zone_id}/dns_records - Query: {request.args}")
    """
    Lista los registros DNS de una zona.
    
    Args:
        zone_id (str): ID de la zona DNS.
        
    Query Parameters:
        type (str, opcional): Filtra los registros por tipo (A, CNAME, etc.).
        name (str, opcional): Filtra los registros por nombre.
        
    Returns:
        JSON: Lista de registros DNS que coinciden con los filtros.
    """
    # Verificar autenticación
    error, status = _verify_auth()
    if error:
        return jsonify(error), status
    
    # Obtener parámetros de consulta
    record_type = request.args.get('type')
    record_name = request.args.get('name')
    
    # Obtener registros de la zona
    records = MOCK_DNS_RECORDS.get(zone_id, [])
    
    # Filtrar registros según los parámetros
    filtered_records = []
    for record in records:
        # Aplicar filtros
        if record_type and record["type"] != record_type:
            continue
            
        if record_name and record["name"] != record_name:
            continue
        
        # Construir respuesta con el formato de la API real
        record_data = {
            "id": record["id"],
            "type": record["type"],
            "name": record["name"],
            "content": record["content"],
            "proxiable": True,
            "proxied": record.get("proxied", False),
            "ttl": record.get("ttl", 1),
            "locked": False,
            "zone_id": zone_id,
            "zone_name": next(
                (z["name"] for z in MOCK_ZONES if z["id"] == zone_id),
                "binarius.cl"
            ),
            "created_on": record.get("created_on", datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')),
            "modified_on": record.get("modified_on", datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')),
            "meta": {
                "auto_added": False,
                "managed_by_apps": False,
                "managed_by_argo_tunnel": False,
                "source": "primary"
            }
        }
        filtered_records.append(record_data)
    
    return jsonify({
        "success": True,
        "errors": [],
        "messages": [],
        "result": filtered_records,
        "result_info": {
            "page": 1,
            "per_page": 100,
            "count": len(filtered_records),
            "total_count": len(filtered_records),
            "total_pages": 1
        }
    })

@dns_records_bp.route('/zones/<zone_id>/dns_records/<record_id>', methods=['PUT'])
def update_dns_record(zone_id, record_id):
    print(f"[DEBUG] PUT /zones/{zone_id}/dns_records/{record_id} - Body: {request.json}")
    """
    Actualiza un registro DNS existente.
    
    Args:
        zone_id (str): ID de la zona DNS.
        record_id (str): ID del registro DNS a actualizar.
        
    Request Body:
        JSON con los campos a actualizar (type, name, content, ttl, proxied).
        
    Returns:
        JSON: El registro actualizado o un mensaje de error.
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
    
    # Validar el cuerpo de la solicitud
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False, 
            "errors": [{"code": 6003, "message": "Invalid request body"}],
            "messages": [{"code": 6003, "message": "Invalid request body"}],
            "result": None
        }), 400
    
    # Permitir tanto formato plano como envelope {'record': {...}}
    if 'record' in data and isinstance(data['record'], dict):
        record_data = data['record']
    else:
        record_data = data

    # Validar campos requeridos (solo 'type', 'name', 'content' son estrictos)
    required_fields = ['type', 'name', 'content']
    missing_fields = [field for field in required_fields if field not in record_data]
    if missing_fields:
        return jsonify({
            "success": False, 
            "errors": [{"code": 1004, "message": f"Missing required fields: {', '.join(missing_fields)}"}],
            "messages": [{"code": 1004, "message": f"Missing required fields: {', '.join(missing_fields)}"}],
            "result": None
        }), 400
    # Asignar valores por defecto si faltan 'ttl' o 'proxied'
    if 'ttl' not in record_data:
        record_data['ttl'] = 1
    if 'proxied' not in record_data:
        record_data['proxied'] = False

    # Validar que el tipo sea A (solo soportamos A records por ahora)
    if record_data['type'] != 'A':
        return jsonify({
            "success": False,
            "errors": [{"code": 1005, "message": "Only A records supported in mock"}],
            "messages": [{"code": 1005, "message": "Only A records supported in mock"}],
            "result": None
        }), 400
    
    # Buscar la zona
    zone_records = MOCK_DNS_RECORDS.get(zone_id, [])
    # Buscar el registro a actualizar
    record_to_update = next((r for r in zone_records if r["id"] == record_id), None)
    if not record_to_update:
        return jsonify({
            "success": False, 
            "errors": [{"code": 81044, "message": "Record not found"}],
            "messages": [{"code": 81044, "message": "Record not found"}],
            "result": None
        }), 404
    
    # Validar que el nombre del registro pertenezca al dominio de la zona
    zone_name = next((z["name"] for z in zones.MOCK_ZONES if z["id"] == zone_id), "")
    record_name = record_data['name']
    
    if not (record_name == zone_name or record_name.endswith('.' + zone_name)):
        return jsonify({
            "success": False,
            "errors": [{"code": 1004, "message": "DNS Validation Error: Record name does not belong to zone"}],
            "messages": [{"code": 1004, "message": "DNS Validation Error: Record name does not belong to zone"}],
            "result": None
        }), 400
    
    # Actualizar el registro
    record_to_update.update({
        "name": record_name,
        "type": record_data['type'],
        "content": record_data['content'],
        "ttl": int(record_data['ttl']),
        "proxied": bool(record_data['proxied']),
        "modified_on": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    })
    
    # Devolver el registro actualizado en el formato correcto (idéntico a Cloudflare)
    return jsonify({
        "success": True,
        "errors": [],
        "messages": [
            {
                "code": 1000,
                "message": "DNS record updated",
                "type": None
            }
        ],
        "result": {
            "id": record_id,
            "zone_id": zone_id,
            "zone_name": zone_name,
            "name": record_name,
            "type": record_data['type'],
            "content": record_data['content'],
            "proxiable": True,
            "proxied": bool(record_data['proxied']),
            "ttl": int(record_data['ttl']),
            "comment": record_data.get("comment", None),
            "settings": {},
            "tags": record_data.get("tags", []),
            "meta": {},
            "locked": False,
            "created_on": record_to_update.get("created_on", datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')),
            "modified_on": record_to_update["modified_on"]
        }
    })

# Importar zonas al final para evitar dependencias circulares
from . import zones
