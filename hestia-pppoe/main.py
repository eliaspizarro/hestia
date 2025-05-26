# main.py
# Flujo principal para la actualización de registros DNS en Cloudflare usando datos de HestiaCP
# Todos los comentarios y mensajes están en español.

import sys
from config import (
    CLOUDFLARE_API_TOKEN,
    CLOUDFLARE_API_BASE_URL,
    CLOUDFLARE_EXCLUDED_DOMAINS,
    V_LIST_USERS_PATH,
    V_LIST_WEB_DOMAINS_PATH,
    V_UPDATE_SYS_IP_PATH,
    IP_SERVICE_URLS,
    logger
)
from hestia_cli import list_users, list_web_domains, update_hestia_system_ip
from cloudflare_dns import list_zones, list_dns_records, update_dns_record, find_zone_for_domain
from filter_utils import filter_excluded
from ip_utils import get_external_ip
import os
import subprocess


def main():
    try:
        logger.info("Iniciando actualización de registros DNS en Cloudflare...")
        # Obtener la IP pública real
        nueva_ip = get_external_ip(IP_SERVICE_URLS)
        if not nueva_ip:
            logger.error("No se pudo obtener la IP pública. Saliendo...")
            sys.exit(1)
        logger.info(f"IP pública detectada: {nueva_ip}")

        # 1. Obtener usuarios de Hestia
        usuarios = list_users(cmd_path=V_LIST_USERS_PATH)
        logger.info(f"Usuarios Hestia encontrados: {usuarios}")

        # 2. Obtener dominios y alias gestionados por cada usuario
        hestia_domains = []
        for user in usuarios:
            dominios = list_web_domains(user, cmd_path=V_LIST_WEB_DOMAINS_PATH)
            for d in dominios:
                hestia_domains.append(d['DOMAIN'])
                hestia_domains.extend(d['ALIASES'])
        logger.info(f"Dominios y alias gestionados por Hestia: {hestia_domains}")

        # 3. Filtrar dominios y alias excluidos
        excluidos = CLOUDFLARE_EXCLUDED_DOMAINS  # Ya es una lista procesada en config.py
        hestia_domains_filtrados = filter_excluded(hestia_domains, excluidos)
        logger.info(f"Dominios tras exclusión: {hestia_domains_filtrados}")

        # 4. Obtener zonas de Cloudflare y mapear dominios a sus zonas
        dominios_por_zona = {}
        for dominio in hestia_domains_filtrados:
            zona = find_zone_for_domain(CLOUDFLARE_API_BASE_URL, CLOUDFLARE_API_TOKEN, dominio)
            if not zona:
                logger.warning(f"No se encontró zona para el dominio {dominio}, omitiendo...")
                continue
            
            if zona['name'] not in dominios_por_zona:
                dominios_por_zona[zona['name']] = {
                    'zone_id': zona['id'],
                    'dominios': []
                }
            dominios_por_zona[zona['name']]['dominios'].append(dominio)
        
        logger.info(f"Zonas a actualizar: {list(dominios_por_zona.keys())}")

        # 5. Para cada zona, obtener registros DNS y actualizar
        for zona_nombre, zona_info in dominios_por_zona.items():
            logger.info(f"Procesando zona: {zona_nombre} ({zona_info['zone_id']})")
            
            # Obtener registros DNS para los dominios de esta zona
            for dominio in zona_info['dominios']:
                registros = list_dns_records(
                    CLOUDFLARE_API_BASE_URL, 
                    CLOUDFLARE_API_TOKEN, 
                    zona_info['zone_id'],
                    name=dominio
                )
                
                # Filtrar solo registros A que coincidan exactamente con el dominio
                registros_filtrados = [
                    r for r in registros 
                    if r['type'] == 'A' and r['name'] == dominio
                ]
                
                # Actualizar cada registro
                for record in registros_filtrados:
                    if record['content'] == nueva_ip:
                        logger.info(f"El registro A para {dominio} ya está actualizado con la IP {nueva_ip}")
                        continue
                        
                    logger.info(f"Actualizando registro A: {dominio} ({record['id']}) en zona {zona_nombre} con IP {nueva_ip}")
                    try:
                        resultado = update_dns_record(
                            CLOUDFLARE_API_BASE_URL,
                            CLOUDFLARE_API_TOKEN,
                            zona_info['zone_id'],
                            record['id'],
                            dominio,
                            nueva_ip,
                            ttl=1,
                            proxied=False
                        )
                        logger.debug(f"Respuesta Cloudflare: {resultado}")
                    except Exception as e:
                        logger.error(f"Error al actualizar registro {dominio} en zona {zona_nombre}: {e}")

        logger.info("Actualización de registros DNS completada.")

        # Sincronizar la IP del sistema en HestiaCP al final del flujo
        update_hestia_system_ip(V_UPDATE_SYS_IP_PATH, logger)

    except Exception as e:
        logger.error(f"Error en el flujo principal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
