"""
Cliente LLM para OpenAI.
"""

import os
import tiktoken
from typing import List, Any, Dict, Optional
from openai import OpenAI, OpenAIError
from .base import LLMClient, ChatMessage
from .retry import retry_with_backoff, handle_http_errors
from .cache import global_cache
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
        
        # Inicializar tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback para modelos no reconocidos
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def get_model_name(self) -> str:
        """
        Obtiene el nombre del modelo utilizado.
        
        Returns:
            str: Nombre del modelo
        """
        return self.model
    
    def get_token_count(self, text: str) -> int:
        """
        Estima el número de tokens en un texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            int: Número estimado de tokens
        """
        if not text:
            return 0
        return len(self.tokenizer.encode(text))
    
    @retry_with_backoff(max_retries=3)
    @handle_http_errors
    def chat(
        self, 
        messages: List[ChatMessage], 
        use_cache: bool = True,
        **params: Any
    ) -> str:
        """
        Envía mensajes al modelo de OpenAI y obtiene una respuesta.
        
        Args:
            messages: Lista de mensajes para el chat
            use_cache: Si se debe usar la caché
            **params: Parámetros adicionales (temperature, max_tokens, etc.)
            
        Returns:
            str: Respuesta del modelo
            
        Raises:
            LLMError: Si ocurre un error en la comunicación con la API
            RateLimitError: Si se excede el límite de tasa
            AuthenticationError: Si hay un error de autenticación
            ModelError: Si hay un error con el modelo
        """
        # Verificar caché primero
        if use_cache:
            cached_response = global_cache.get(messages, self.model, params)
            if cached_response:
                return cached_response
        
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
            
            result = response.choices[0].message.content
            
            # Guardar en caché si está habilitado
            if use_cache and result:
                global_cache.set(messages, self.model, params, result)
            
            return result
            
        except OpenAIError as e:
            if "rate_limit" in str(e).lower():
                raise RateLimitError(f"Límite de tasa excedido: {e}")
            elif "authentication" in str(e).lower():
                raise AuthenticationError(f"Error de autenticación: {e}")
            elif "model" in str(e).lower():
                raise ModelError(f"Error del modelo: {e}")
            else:
                raise LLMError(f"Error de OpenAI: {e}") 