import os
import json
from flask import Blueprint, request

bp = Blueprint('ip', __name__)

def get_ip_from_shared_data():
    """
    Obtiene la IP desde el archivo debug_shared_data.json.
    
    Returns:
        str: La IP actual del servicio o '127.0.0.1' si hay un error
    """
    try:
        # Construir la ruta al archivo de datos compartidos
        current_dir = os.path.dirname(os.path.abspath(__file__))
        shared_data_file = os.path.join(current_dir, 'debug_shared_data.json')
        
        if os.path.exists(shared_data_file):
            with open(shared_data_file, 'r') as f:
                data = json.load(f)
                # Obtener la IP de current_ip_services_ip
                return data.get('current_ip_services_ip', '127.0.0.1')
                
        print(f"[WARNING] No se encontró el archivo: {shared_data_file}")
        return "127.0.0.1"
        
    except Exception as e:
        print(f"[ERROR] Error al cargar la IP desde debug_shared_data.json: {e}")
        return "127.0.0.1"

@bp.route('/ip')
def get_ip():
    """
    Endpoint para obtener la IP actual.
    
    Returns:
        str: La IP actual en formato texto plano
    """
    print(f"[DEBUG] GET /ip - Headers: {dict(request.headers)}")
    ip = get_ip_from_shared_data()
    print(f"[DEBUG] Devolviendo IP: {ip}")
    return f"{ip}\n"

def init_ip_service(app):
    """Inicializa el servicio de IP en la aplicación Flask."""
    app.register_blueprint(bp)
    print("[INFO] Servicio de IP inicializado")
