"""
llm-html-processor - Procesador de HTML multilingüe con LLMs
"""

__version__ = "0.1.0"

from .models import ProcessingOptions, ProcessingResult, TextChunk, CostEstimate
from .pipeline import process_html
from .utils.logging import configure_from_env, get_logger
from .cli import main as cli_main

# Configurar logging desde variables de entorno
configure_from_env()

# API pública
__all__ = [
    "process_html",
    "ProcessingOptions",
    "ProcessingResult",
    "TextChunk",
    "CostEstimate",
    "get_logger",
    "cli_main"
] 