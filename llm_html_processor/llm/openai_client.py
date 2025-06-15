"""
Cliente LLM para OpenAI.
"""

import os
from typing import List, Any
from openai import OpenAI, OpenAIError
from .base import LLMClient, ChatMessage
from .retry import retry_with_backoff, handle_http_errors
from .errors import (
    LLMError,
    RateLimitError,
    AuthenticationError,
    ModelError
)

class OpenAIClient(LLMClient):
    """Cliente para interactuar con modelos de OpenAI."""
    
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        max_retries: int = 3,
        timeout: float = 30.0
    ):
        """
        Inicializa el cliente de OpenAI.
        
        Args:
            api_key: Clave API de OpenAI. Si es None, se busca en OPENAI_API_KEY
            model: Modelo a utilizar
            max_retries: Número máximo de reintentos
            timeout: Tiempo máximo de espera en segundos
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("Se requiere OPENAI_API_KEY")
            
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.client = OpenAI(
            api_key=self.api_key,
            timeout=self.timeout
        )
    
    @retry_with_backoff(max_retries=3)
    @handle_http_errors
    def chat(self, messages: List[ChatMessage], **params: Any) -> str:
        """
        Envía mensajes al modelo de OpenAI y obtiene una respuesta.
        
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
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                **params
            )
            
            return response.choices[0].message.content
            
        except OpenAIError as e:
            if "rate_limit" in str(e).lower():
                raise RateLimitError(f"Límite de tasa excedido: {e}")
            elif "authentication" in str(e).lower():
                raise AuthenticationError(f"Error de autenticación: {e}")
            elif "model" in str(e).lower():
                raise ModelError(f"Error del modelo: {e}")
            else:
                raise LLMError(f"Error de OpenAI: {e}") 