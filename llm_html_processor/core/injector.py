"""
Inyector de texto en documentos HTML.
"""

from bs4 import BeautifulSoup
from typing import List
from ..models import TextChunk

def inject_text(html: str, chunks: List[TextChunk]) -> str:
    """
    Inyecta texto procesado de vuelta en el HTML.
    
    Args:
        html: HTML original como string
        chunks: Lista de fragmentos de texto procesados
        
    Returns:
        str: HTML con el texto inyectado
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # TODO: Implementar búsqueda por path CSS
    for chunk in chunks:
        # Placeholder: reemplazar primer nodo de texto
        for node in soup.find_all(text=True):
            if node.strip():
                node.replace_with(chunk.text)
                break
    
    return str(soup) 