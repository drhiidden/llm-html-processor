"""
Extractor de texto de documentos HTML.
"""

from bs4 import BeautifulSoup
from typing import List
from ..models import TextChunk

def extract_text_nodes(html: str) -> List[TextChunk]:
    """
    Extrae nodos de texto del HTML preservando su estructura.
    
    Args:
        html: Contenido HTML como string
        
    Returns:
        List[TextChunk]: Lista de fragmentos de texto con sus paths
    """
    soup = BeautifulSoup(html, 'html.parser')
    chunks = []
    
    for node in soup.find_all(text=True):
        if node.strip():
            # TODO: Implementar generación de path CSS
            path = "body"  # Placeholder
            chunks.append(TextChunk(
                text=node.strip(),
                path=path,
                is_rtl=node.parent.get('dir', '') == 'rtl'
            ))
    
    return chunks 