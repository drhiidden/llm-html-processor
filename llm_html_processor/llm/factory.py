"""
Fábrica para crear instancias de clientes LLM.
"""

from typing import Literal, Optional
from .base import LLMClient
from .openai_client import OpenAIClient
from .gemini_client import GeminiClient
from .local_client import LocalLLMClient

LLMProvider = Literal["openai", "gemini", "local"]

def create_llm_client(
    provider: LLMProvider,
    model: Optional[str] = None,
    **kwargs
) -> LLMClient:
    """
    Crea una instancia del cliente LLM especificado.
    
    Args:
        provider: Proveedor LLM a utilizar
        model: Nombre del modelo (opcional)
        **kwargs: Argumentos adicionales para el cliente
        
    Returns:
        LLMClient: Instancia del cliente LLM
        
    Raises:
        ValueError: Si el proveedor no es válido
    """
    if provider == "openai":
        return OpenAIClient(model=model or "gpt-4o-mini", **kwargs)
    elif provider == "gemini":
        return GeminiClient(model=model or "gemini-pro", **kwargs)
    elif provider == "local":
        return LocalLLMClient(model=model or "llama2", **kwargs)
    else:
        raise ValueError(f"Proveedor LLM no válido: {provider}") 