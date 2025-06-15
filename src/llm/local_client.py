"""
Cliente LLM para modelos locales vía HTTP.
"""

import json
from typing import List, Any
import httpx
from .base import LLMClient, ChatMessage
from .retry import retry_with_backoff, handle_http_errors
from .errors import (
    LLMError,
    RateLimitError,
    AuthenticationError,
    ModelError
)

class LocalLLMClient(LLMClient):
    """Cliente para interactuar con modelos LLM locales vía HTTP."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2",
        max_retries: int = 3,
        timeout: float = 30.0
    ):
        """
        Inicializa el cliente para LLMs locales.
        
        Args:
            base_url: URL base del servidor LLM (por defecto: Ollama)
            model: Nombre del modelo a utilizar
            max_retries: Número máximo de reintentos
            timeout: Tiempo máximo de espera en segundos
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout
        )
    
    @retry_with_backoff(max_retries=3)
    @handle_http_errors
    def chat(self, messages: List[ChatMessage], **params: Any) -> str:
        """
        Envía mensajes al modelo local y obtiene una respuesta.
        
        Args:
            messages: Lista de mensajes para el chat
            **params: Parámetros adicionales (temperature, max_tokens, etc.)
            
        Returns:
            str: Respuesta del modelo
            
        Raises:
            LLMError: Si ocurre un error en la comunicación con la API
            RateLimitError: Si se excede el límite de tasa
            AuthenticationError: Si hay un error de autenticación
            ModelError: Si hay un error con el modelo
        """
        try:
            # Formato compatible con Ollama
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            response = self.client.post(
                "/api/chat",
                json={
                    "model": self.model,
                    "messages": formatted_messages,
                    **params
                }
            )
            
            if response.status_code != 200:
                error_msg = response.text
                if "rate limit" in error_msg.lower():
                    raise RateLimitError("Límite de tasa excedido")
                elif "authentication" in error_msg.lower():
                    raise AuthenticationError("Error de autenticación")
                elif "model" in error_msg.lower():
                    raise ModelError("Error del modelo")
                else:
                    raise LLMError(f"Error del servidor: {error_msg}")
                    
            return response.json()["message"]["content"]
            
        except httpx.RequestError as e:
            raise LLMError(f"Error de conexión: {e}")
        except json.JSONDecodeError as e:
            raise LLMError(f"Error al decodificar respuesta: {e}")
        except KeyError as e:
            raise LLMError(f"Respuesta mal formada: {e}") 