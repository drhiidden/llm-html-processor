"""
Módulo para manejar reintentos y errores comunes en clientes LLM.
"""

import time
from functools import wraps
from typing import Type, Callable, Any, Optional
import httpx
from openai import OpenAIError
from google.genai.types import exceptions as genai_exceptions
from .errors import (
    LLMError,
    RateLimitError,
    AuthenticationError,
    ModelError
)

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorador para reintentar operaciones con backoff exponencial.
    
    Args:
        max_retries: Número máximo de reintentos
        initial_delay: Retraso inicial en segundos
        max_delay: Retraso máximo en segundos
        backoff_factor: Factor de multiplicación para el retraso
        exceptions: Tupla de excepciones a capturar
        
    Returns:
        Callable: Función decorada
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                        
                    # Convertir excepciones específicas
                    if isinstance(e, OpenAIError):
                        if "rate_limit" in str(e).lower():
                            raise RateLimitError(f"Límite de tasa excedido: {e}")
                        elif "authentication" in str(e).lower():
                            raise AuthenticationError(f"Error de autenticación: {e}")
                        elif "model" in str(e).lower():
                            raise ModelError(f"Error del modelo: {e}")
                    elif isinstance(e, genai_exceptions.GenAIError):
                        if isinstance(e, genai_exceptions.RateLimitError):
                            raise RateLimitError(f"Límite de tasa excedido: {e}")
                        elif isinstance(e, genai_exceptions.AuthenticationError):
                            raise AuthenticationError(f"Error de autenticación: {e}")
                        elif isinstance(e, genai_exceptions.ModelError):
                            raise ModelError(f"Error del modelo: {e}")
                        else:
                            raise LLMError(f"Error de Gemini API: {e}")
                    
                    # Esperar con backoff exponencial
                    time.sleep(min(delay, max_delay))
                    delay *= backoff_factor
            
            # Si llegamos aquí, todos los reintentos fallaron
            raise LLMError(f"Todos los reintentos fallaron: {last_exception}")
            
        return wrapper
    return decorator

def handle_http_errors(func: Callable) -> Callable:
    """
    Decorador para manejar errores HTTP comunes.
    
    Args:
        func: Función a decorar
        
    Returns:
        Callable: Función decorada
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Límite de tasa excedido")
            elif e.response.status_code == 401:
                raise AuthenticationError("Error de autenticación")
            elif e.response.status_code == 404:
                raise ModelError("Modelo no encontrado")
            else:
                raise LLMError(f"Error HTTP {e.response.status_code}: {e}")
        except httpx.RequestError as e:
            raise LLMError(f"Error de conexión: {e}")
            
    return wrapper 