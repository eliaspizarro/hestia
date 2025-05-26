import json
import os
from pathlib import Path

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_zones(zones_file):
    """Extrae información de zonas del archivo de zonas de Cloudflare."""
    data = load_json_file(zones_file)
    zones = {}
    for zone in data.get('result', []):
        zones[zone['name']] = {
            'id': zone['id'],
            'name': zone['name'],
            'status': zone['status']
        }
    return zones

def extract_dns_records(dns_dir, zones):
    """Extrae registros DNS de los archivos de registros DNS de Cloudflare."""
    dns_data = {}
    
    for zone_name, zone_info in zones.items():
        # Construir el nombre del archivo de registros DNS para esta zona
        dns_file = f"20250525_231847_dns_records_{zone_name}_p1.json"
        dns_path = os.path.join(dns_dir, dns_file)
        
        if not os.path.exists(dns_path):
            print(f"Advertencia: No se encontró el archivo de registros DNS para {zone_name}")
            continue
        
        # Cargar los registros DNS
        dns_content = load_json_file(dns_path)
        
        # Filtrar solo registros A
        a_records = [
            {
                'name': record['name'],
                'content': record['content'],
                'type': record['type'],
                'id': record['id']
            }
            for record in dns_content.get('result', [])
            if record['type'] == 'A'
        ]
        
        if a_records:
            dns_data[zone_name] = a_records
    
    return dns_data

def update_shared_data(shared_data_path, dns_data):
    """Actualiza el archivo de datos compartidos con la información de DNS."""
    # Cargar el archivo existente
    with open(shared_data_path, 'r', encoding='utf-8') as f:
        shared_data = json.load(f)
    
    # Actualizar la sección de dominios de Cloudflare
    cloudflare_domains = {}
    for zone, records in dns_data.items():
        cloudflare_domains[zone] = [
            {'name': r['name'], 'content': r['content']}
            for r in records
        ]
    
    shared_data['cloudflare_domains'] = cloudflare_domains
    
    # Guardar los cambios
    with open(shared_data_path, 'w', encoding='utf-8') as f:
        json.dump(shared_data, f, indent=2, ensure_ascii=False)
    
    print(f"Se actualizó el archivo {shared_data_path} con éxito.")

def main():
    # Rutas de los archivos
    base_dir = Path(__file__).parent.parent.parent  # Directorio raíz del proyecto
    examples_dir = base_dir / 'examples' / 'cloudflare_api'
    debug_data_path = base_dir / 'tests' / 'scripts' / 'debug_shared_data.json'
    
    # Extraer información de zonas
    zones_file = examples_dir / '20250525_231847_zones_full.json'
    zones = extract_zones(zones_file)
    
    # Extraer registros DNS
    dns_data = extract_dns_records(examples_dir, zones)
    
    # Actualizar el archivo de datos compartidos
    update_shared_data(debug_data_path, dns_data)

if __name__ == "__main__":
    main()
