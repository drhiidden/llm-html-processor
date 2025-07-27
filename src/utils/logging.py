"""
Sistema de logging configurable.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Literal, Dict, Any

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class LogConfig:
    """Configuración de logging."""
    
    def __init__(
        self,
        level: LogLevel = "INFO",
        log_file: Optional[str] = None,
        console: bool = True,
        format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ):
        """
        Inicializa la configuración de logging.
        
        Args:
            level: Nivel de logging
            log_file: Archivo de log (opcional)
            console: Si se debe mostrar en consola
            format: Formato de los mensajes
        """
        self.level = level
        self.log_file = log_file
        self.console = console
        self.format = format

def setup_logging(
    name: str = "llm_html_processor",
    config: Optional[LogConfig] = None
) -> logging.Logger:
    """
    Configura y devuelve un logger.
    
    Args:
        name: Nombre del logger
        config: Configuración personalizada
        
    Returns:
        logging.Logger: Logger configurado
    """
    config = config or LogConfig()
    
    # Crear logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.level))
    
    # Limpiar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Crear formatter
    formatter = logging.Formatter(config.format)
    
    # Añadir handler de consola si está habilitado
    if config.console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Añadir handler de archivo si está configurado
    if config.log_file:
        # Asegurar que el directorio existe
        log_path = Path(config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Logger global por defecto
default_logger = setup_logging()

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Obtiene un logger configurado.
    
    Args:
        name: Nombre del logger (opcional)
        
    Returns:
        logging.Logger: Logger configurado
    """
    if name:
        return logging.getLogger(f"llm_html_processor.{name}")
    return default_logger

def configure_from_env() -> None:
    """Configura el logging desde variables de entorno."""
    level = os.getenv("LLM_LOG_LEVEL", "INFO")
    log_file = os.getenv("LLM_LOG_FILE")
    console = os.getenv("LLM_LOG_CONSOLE", "1") == "1"
    
    config = LogConfig(
        level=level,  # type: ignore
        log_file=log_file,
        console=console
    )
    
    global default_logger
    default_logger = setup_logging(config=config) 