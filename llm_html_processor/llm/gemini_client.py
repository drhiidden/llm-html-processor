"""
Cliente LLM para Google Gemini.
"""

import os
from typing import List, Any, Optional
from google import genai
from google.genai import types
from google.genai.types import exceptions as genai_exceptions
from .base import LLMClient, ChatMessage
from .retry import retry_with_backoff, handle_http_errors
from .errors import (
    LLMError,
    RateLimitError,
    AuthenticationError,
    ModelError
)

class GeminiClient(LLMClient):
    """Cliente para interactuar con modelos de Google Gemini."""
    
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-pro",
        max_retries: int = 3,
        timeout: float = 30.0,
        generation_config: Optional[types.GenerationConfig] = None
    ):
        """
        Inicializa el cliente de Gemini.
        
        Args:
            api_key: Clave API de Google. Si es None, se busca en GOOGLE_API_KEY
            model: Modelo a utilizar
            max_retries: Número máximo de reintentos
            timeout: Tiempo máximo de espera en segundos
            generation_config: Configuración de generación personalizada
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Se requiere GOOGLE_API_KEY")
            
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Configurar el cliente
        genai.configure(api_key=self.api_key)
        
        # Configuración por defecto de generación
        self.default_generation_config = generation_config or types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=2048,
            top_p=0.95,
            top_k=40
        )
        
        # Inicializar el modelo
        self.client = genai.GenerativeModel(
            model_name=self.model,
            generation_config=self.default_generation_config
        )
    
    def _create_generation_config(self, params: dict[str, Any]) -> types.GenerationConfig:
        """
        Crea una configuración de generación a partir de los parámetros.
        
        Args:
            params: Parámetros de generación
            
        Returns:
            types.GenerationConfig: Configuración de generación
        """
        return types.GenerationConfig(
            temperature=params.get("temperature", self.default_generation_config.temperature),
            max_output_tokens=params.get("max_tokens", self.default_generation_config.max_output_tokens),
            top_p=params.get("top_p", self.default_generation_config.top_p),
            top_k=params.get("top_k", self.default_generation_config.top_k)
        )
    
    @retry_with_backoff(max_retries=3)
    @handle_http_errors
    def chat(self, messages: List[ChatMessage], **params: Any) -> str:
        """
        Envía mensajes al modelo de Gemini y obtiene una respuesta.
        
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
            # Crear configuración de generación
            generation_config = self._create_generation_config(params)
            
            # Iniciar chat
            chat = self.client.start_chat(
                history=[],
                generation_config=generation_config
            )
            
            # Procesar mensajes
            last_response = None
            for msg in messages:
                if msg.role == "user":
                    response = chat.send_message(
                        msg.content,
                        generation_config=generation_config
                    )
                    last_response = response
                elif msg.role == "assistant":
                    # En Gemini, las respuestas del asistente se manejan automáticamente
                    continue
                else:
                    raise ValueError(f"Rol no soportado: {msg.role}")
            
            if not last_response:
                raise LLMError("No se recibió respuesta del modelo")
                
            return last_response.text
            
        except genai_exceptions.RateLimitError as e:
            raise RateLimitError(f"Límite de tasa excedido: {e}")
        except genai_exceptions.AuthenticationError as e:
            raise AuthenticationError(f"Error de autenticación: {e}")
        except genai_exceptions.ModelError as e:
            raise ModelError(f"Error del modelo: {e}")
        except genai_exceptions.GenAIError as e:
            raise LLMError(f"Error de Gemini API: {e}")
        except Exception as e:
            raise LLMError(f"Error inesperado: {e}") 