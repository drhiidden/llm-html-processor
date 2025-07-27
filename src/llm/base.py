"""
Interfaz base para clientes LLM.
"""

from typing import Protocol, List, Dict, Any, Optional

class ChatMessage:
    """Mensaje para el chat con el LLM."""
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

class LLMClient(Protocol):
    """Interfaz base para clientes LLM."""
    
    def chat(
        self, 
        messages: List[ChatMessage], 
        use_cache: bool = True,
        **params: Any
    ) -> str:
        """
        Envía mensajes al LLM y obtiene una respuesta.
        
        Args:
            messages: Lista de mensajes para el chat
            use_cache: Si se debe usar la caché
            **params: Parámetros adicionales específicos del modelo
            
        Returns:
            str: Respuesta del modelo
        """
        ...
        
    def get_model_name(self) -> str:
        """
        Obtiene el nombre del modelo utilizado.
        
        Returns:
            str: Nombre del modelo
        """
        ...
        
    def get_token_count(self, text: str) -> int:
        """
        Estima el número de tokens en un texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            int: Número estimado de tokens
        """
        ... 