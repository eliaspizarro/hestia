# hestia_cli.py
# Funciones para interactuar con la CLI de HestiaCP y utilidades relacionadas
# Todos los comentarios y documentación estarán en español.

import json
import subprocess
from typing import List, Dict, Any
from filter_utils import filter_excluded
import os


def update_hestia_system_ip(v_update_sys_ip_path: str, logger) -> bool:
    """
    Ejecuta el script v-update-sys-ip para sincronizar la IP del sistema en HestiaCP.
    Registra el resultado usando el logger proporcionado.
    Devuelve True si la ejecución fue exitosa, False en caso contrario.
    """
    if v_update_sys_ip_path and os.path.exists(v_update_sys_ip_path):
        try:
            logger.info(f"Ejecutando sincronización de IP en HestiaCP: {v_update_sys_ip_path}")
            result = subprocess.run([v_update_sys_ip_path], capture_output=True, text=True, check=True)
            logger.info("Sincronización de IP en HestiaCP completada exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error al ejecutar v-update-sys-ip: {e}")
    else:
        logger.warning(f"No se encontró el binario v-update-sys-ip en {v_update_sys_ip_path}, omitiendo actualización de IP en HestiaCP.")
    return False


def list_users(cmd_path: str = "v-list-users", use_json: bool = True) -> List[str]:
    """
    Ejecuta la CLI de HestiaCP para obtener la lista de usuarios. Devuelve una lista de nombres de usuario.
    """
    args = [cmd_path]
    if use_json:
        args.append("json")
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return list(data.keys())


def list_web_domains(user: str, cmd_path: str = "v-list-web-domains", use_json: bool = True) -> List[Dict[str, Any]]:
    """
    Ejecuta la CLI de HestiaCP para obtener los dominios y alias de un usuario.
    Devuelve una lista de diccionarios con los dominios y sus alias.
    """
    args = [cmd_path, user]
    if use_json:
        args.append("json")
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    dominios = []
    for dominio, props in data.items():
        aliases = []
        if 'ALIAS' in props and props['ALIAS']:
            # Puede ser string separado por coma o espacio
            aliases = [a.strip() for a in props['ALIAS'].replace(',', ' ').split() if a.strip()]
        dominios.append({
            'DOMAIN': dominio,
            'ALIASES': aliases
        })
    return dominios


def get_all_hestia_domains(users: List[str]) -> List[str]:
    """
    Devuelve una lista de todos los dominios y alias gestionados por todos los usuarios de Hestia.
    """
    todos = []
    for user in users:
        dominios = list_web_domains(user)
        for d in dominios:
            todos.append(d['DOMAIN'])
            todos.extend(d['ALIASES'])
    return todos

