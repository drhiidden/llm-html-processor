"""
Interfaz base para clientes LLM.
"""

from typing import Protocol, List, Dict, Any

class ChatMessage:
    """Mensaje para el chat con el LLM."""
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

class LLMClient(Protocol):
    """Interfaz base para clientes LLM."""
    
    def chat(self, messages: List[ChatMessage], **params: Any) -> str:
        """
        Envía mensajes al LLM y obtiene una respuesta.
        
        Args:
            messages: Lista de mensajes para el chat
            **params: Parámetros adicionales específicos del modelo
            
        Returns:
            str: Respuesta del modelo
        """
        ... 