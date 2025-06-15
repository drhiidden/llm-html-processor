"""
Modelos de datos para el procesador de HTML.
"""

from dataclasses import dataclass
from typing import Literal, Optional

@dataclass
class ProcessingOptions:
    """Opciones para el procesamiento de HTML."""
    task: Literal["paraphrase", "summarize", "custom"]
    language: str = "he"
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2048
    preserve_html: bool = True
    extra_prompt: Optional[str] = None

@dataclass
class TextChunk:
    """Fragmento de texto extraído del HTML."""
    text: str
    path: str  # Selector CSS-like para localizar el nodo
    is_rtl: bool = False

@dataclass
class ProcessingResult:
    """Resultado del procesamiento de HTML."""
    html: str
    stats: dict  # Estadísticas de procesamiento (tokens, costes, etc.) 