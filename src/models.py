"""
Modelos de datos para el procesador de HTML.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional, Dict, Any

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
    use_cache: bool = True
    min_text_length: int = 2  # Longitud mínima de texto para procesar

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
    stats: Dict[str, Any] = field(default_factory=dict)  # Estadísticas de procesamiento (tokens, costes, etc.)

@dataclass
class CostEstimate:
    """Estimación de costos para el procesamiento."""
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    model: str = ""
    
    @property
    def total_tokens(self) -> int:
        """Total de tokens (entrada + salida)."""
        return self.input_tokens + self.output_tokens 