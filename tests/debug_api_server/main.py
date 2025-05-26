import os
import sys
from flask import Flask, request, jsonify
import json
from datetime import datetime, timezone

# Agregar el directorio raíz al path para importar los módulos
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Importar blueprints locales
from .cloudflare_api import blueprints as cloudflare_blueprints
from .ip_service import init_ip_service, bp as ip_bp, get_ip_from_shared_data

# Crear la aplicación Flask
app = Flask(__name__)

# Configuración
app.config['DEBUG'] = True

# Ruta al archivo de datos compartidos
SHARED_DATA_FILE = os.path.join(os.path.dirname(__file__), 'debug_shared_data.json')

def save_shared_data(data):
    """Guarda datos en el archivo compartido."""
    with open(SHARED_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_shared_data():
    """Carga datos desde el archivo compartido."""
    if os.path.exists(SHARED_DATA_FILE):
        with open(SHARED_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

# Registrar blueprints de la API de Cloudflare
for bp in cloudflare_blueprints:
    app.register_blueprint(bp, url_prefix='/client/v4')

# Endpoint para obtener la IP actual en texto plano
@app.route('/ip', methods=['GET'])
def get_ip():
    """Devuelve la IP actual en texto plano."""
    print(f"[DEBUG] GET /ip - Headers: {dict(request.headers)}")
    ip = get_ip_from_shared_data()
    print(f"[DEBUG] Devolviendo IP: {ip}")
    return f"{ip}\n", 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    # Obtener el puerto de la variable de entorno o usar 5000 por defecto
    port = int(os.environ.get('PORT', 5000))
    
    # Iniciar el servidor
    print(f"Iniciando servidor de depuración en http://localhost:{port}")
    print("Endpoints disponibles:")
    print(f"  - GET  http://localhost:{port}/ip")
    print("\nEndpoints de la API de Cloudflare (requieren autenticación):")
    print(f"  - GET  http://localhost:{port}/client/v4/zones")
    print(f"  - GET  http://localhost:{port}/client/v4/zones/<zone_id>/dns_records")
    print(f"  - PUT  http://localhost:{port}/client/v4/zones/<zone_id>/dns_records/<record_id>")

    app.run(host='0.0.0.0', port=port, debug=True)
