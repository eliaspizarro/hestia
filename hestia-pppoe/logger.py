import syslog
import os
import sys
from typing import Optional

# Nivel de log por defecto
_DEFAULT_LOG_LEVEL = syslog.LOG_INFO
_APP_NAME = "hestia-pppoe"

# Mapeo de niveles de log
LOG_LEVELS = {
    'DEBUG': syslog.LOG_DEBUG,
    'INFO': syslog.LOG_INFO,
    'WARNING': syslog.LOG_WARNING,
    'ERROR': syslog.LOG_ERR,
    'CRITICAL': syslog.LOG_CRIT
}

class HestiaLogger:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._log_level = LOG_LEVELS.get(
                os.getenv("LOG_LEVEL", "INFO").upper(),
                _DEFAULT_LOG_LEVEL
            )
            self._configure_syslog()

    def set_log_level(self, log_level_str: str):
        """
        Establece el nivel de log. El valor debe ser un string válido ya validado (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        La validación debe hacerse en config.py u otro lugar antes de llamar a este método.
        """
        self._log_level = LOG_LEVELS[log_level_str]

    def _configure_syslog(self):
        """Configura el logger para usar syslog con el formato requerido."""
        # Configurar syslog con las opciones necesarias
        # - LOG_PID: Incluir el ID del proceso
        # - LOG_CONS: Enviar a la consola si no se puede enviar a syslog
        # - LOG_NDELAY: Conectar inmediatamente al servidor syslog
        syslog.openlog(
            ident=_APP_NAME,
            logoption=syslog.LOG_PID | syslog.LOG_CONS | syslog.LOG_NDELAY,
            facility=syslog.LOG_DAEMON
        )

    def _get_log_level(self, level: str):
        """Obtiene el nivel de log correspondiente."""
        return LOG_LEVELS.get(level.upper(), _DEFAULT_LOG_LEVEL)

    def log(self, level: int, message: str, name: str = "main"):
        """
        Registra un mensaje con el nivel especificado.
        
        Args:
            level: Nivel de log (ej. syslog.LOG_INFO)
            message: Mensaje a registrar
            name: Nombre del módulo que genera el log
        """
        if level > self._log_level:
            return
            
        # Formato: (nombre_componente) mensaje
        # El resto del formato lo maneja syslog automáticamente
        formatted_message = f"({name}) {message}"
        syslog.syslog(level, formatted_message)

    def debug(self, message: str, name: str = "main"):
        """Registra un mensaje de depuración."""
        self.log(syslog.LOG_DEBUG, message, name)

    def info(self, message: str, name: str = "main"):
        """Registra un mensaje informativo."""
        self.log(syslog.LOG_INFO, message, name)

    def warning(self, message: str, name: str = "main"):
        """Registra un mensaje de advertencia."""
        self.log(syslog.LOG_WARNING, message, name)

    def error(self, message: str, name: str = "main"):
        """Registra un mensaje de error."""
        self.log(syslog.LOG_ERR, message, name)

    def critical(self, message: str, name: str = "main"):
        """Registra un mensaje crítico."""
        self.log(syslog.LOG_CRIT, message, name)

# Instancia global
hestia_logger = HestiaLogger()

def get_logger(name: str = "main"):
    """
    Función de conveniencia para obtener un logger.
    
    Args:
        name: Nombre del módulo (generalmente __name__)
        
    Returns:
        Objeto logger con métodos para diferentes niveles de log
    """
    # Limitar la longitud del nombre del módulo para mayor legibilidad
    if name == "__main__":
        name = "main"
    elif name.startswith("hestia."):
        name = name[len("hestia."):]
    
    class LoggerWrapper:
        def __init__(self, name):
            self.name = name
            
        def debug(self, message, *args, **kwargs):
            if 'exc_info' in kwargs:
                exc_info = kwargs.pop('exc_info')
                if exc_info:
                    message = f"{message}\n{str(exc_info)}"
            hestia_logger.debug(message, self.name)
            
        def info(self, message, *args, **kwargs):
            if 'exc_info' in kwargs:
                exc_info = kwargs.pop('exc_info')
                if exc_info:
                    message = f"{message}\n{str(exc_info)}"
            hestia_logger.info(message, self.name)
            
        def warning(self, message, *args, **kwargs):
            if 'exc_info' in kwargs:
                exc_info = kwargs.pop('exc_info')
                if exc_info:
                    message = f"{message}\n{str(exc_info)}"
            hestia_logger.warning(message, self.name)
            
        def error(self, message, *args, **kwargs):
            if 'exc_info' in kwargs:
                exc_info = kwargs.pop('exc_info')
                if exc_info:
                    message = f"{message}\n{str(exc_info)}"
            hestia_logger.error(message, self.name)
            
        def critical(self, message, *args, **kwargs):
            if 'exc_info' in kwargs:
                exc_info = kwargs.pop('exc_info')
                if exc_info:
                    import traceback
                    message = f"{message}\n{''.join(traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__))}"
            hestia_logger.critical(message, self.name)
    
    return LoggerWrapper(name)
