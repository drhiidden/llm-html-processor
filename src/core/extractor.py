"""
Extractor de texto de documentos HTML.
"""

import re
from bs4 import BeautifulSoup, Tag, NavigableString, ParserError
from typing import List, Optional
from ..models import TextChunk
from .errors import MalformedHTMLError, EmptyHTMLError, HTMLTooLargeError
from ..utils.logging import get_logger

logger = get_logger("extractor")

# Constantes para validación
MAX_HTML_SIZE = 10 * 1024 * 1024  # 10 MB
MIN_HTML_SIZE = 10  # 10 bytes

def _generate_css_path(node: Tag) -> str:
    """
    Genera un path CSS único para un nodo.
    
    Args:
        node: Nodo BeautifulSoup
        
    Returns:
        str: Path CSS para el nodo
    """
    path_parts = []
    current = node
    
    while current and current.name != "[document]":
        # Obtener el tag
        tag_str = current.name
        
        # Añadir ID si existe
        if current.get('id'):
            tag_str += f"#{current['id']}"
        # Si no hay ID pero hay clase, añadir la primera clase
        elif current.get('class'):
            tag_str += f".{current['class'][0]}"
        # Si no hay ID ni clase, añadir índice entre hermanos del mismo tipo
        else:
            siblings = list(filter(lambda x: x.name == current.name, 
                                  list(current.parent.children) if current.parent else []))
            if len(siblings) > 1:
                index = siblings.index(current) + 1
                tag_str += f":nth-of-type({index})"
                
        path_parts.append(tag_str)
        current = current.parent
        
    return " > ".join(reversed(path_parts))

def _detect_rtl(node: Tag) -> bool:
    """
    Detecta si un nodo tiene contenido RTL.
    
    Args:
        node: Nodo BeautifulSoup
        
    Returns:
        bool: True si es RTL, False en caso contrario
    """
    # Verificar atributos explícitos
    if node.get('dir') == 'rtl':
        return True
    
    # Verificar atributos en padres
    parent = node.parent
    while parent:
        if parent.get('dir') == 'rtl':
            return True
        parent = parent.parent
    
    # Verificar atributos lang que indiquen idiomas RTL comunes
    rtl_langs = ['he', 'ar', 'fa', 'ur']
    lang = node.get('lang') or (node.parent.get('lang') if node.parent else None)
    if lang and any(lang.startswith(rtl) for rtl in rtl_langs):
        return True
    
    # Verificar clases que puedan indicar RTL
    classes = node.get('class', [])
    if any('rtl' in cls.lower() for cls in classes):
        return True
        
    return False

def _sanitize_html(html: str) -> str:
    """
    Sanitiza el HTML para corregir problemas comunes.
    
    Args:
        html: HTML a sanitizar
        
    Returns:
        str: HTML sanitizado
    """
    # Eliminar caracteres nulos
    html = html.replace('\0', '')
    
    # Corregir tags no cerrados comunes
    unclosed_tags = ['img', 'br', 'hr', 'meta', 'input', 'link']
    for tag in unclosed_tags:
        # Reemplazar <tag> por <tag/>
        html = re.sub(f'<{tag}([^>]*[^/])>', f'<{tag}\\1/>', html)
    
    # Corregir atributos sin comillas
    html = re.sub(r'=([^\s>][^\s>]*)', r'="\1"', html)
    
    return html

def _validate_html(html: str) -> None:
    """
    Valida el HTML y lanza excepciones si hay problemas.
    
    Args:
        html: HTML a validar
        
    Raises:
        EmptyHTMLError: Si el HTML está vacío
        HTMLTooLargeError: Si el HTML es demasiado grande
    """
    # Verificar si está vacío
    if not html or len(html.strip()) < MIN_HTML_SIZE:
        raise EmptyHTMLError("El HTML está vacío o es demasiado pequeño")
    
    # Verificar tamaño
    if len(html) > MAX_HTML_SIZE:
        raise HTMLTooLargeError(
            f"El HTML es demasiado grande ({len(html)} bytes)",
            len(html),
            MAX_HTML_SIZE
        )

def extract_text_nodes(html: str, min_text_length: int = 2) -> List[TextChunk]:
    """
    Extrae nodos de texto del HTML preservando su estructura.
    
    Args:
        html: Contenido HTML como string
        min_text_length: Longitud mínima de texto para extraer (evita espacios, etc.)
        
    Returns:
        List[TextChunk]: Lista de fragmentos de texto con sus paths
        
    Raises:
        MalformedHTMLError: Si el HTML está malformado
        EmptyHTMLError: Si el HTML está vacío
        HTMLTooLargeError: Si el HTML es demasiado grande
    """
    # Validar HTML
    _validate_html(html)
    
    # Intentar parsear el HTML
    try:
        soup = BeautifulSoup(html, 'html.parser')
    except ParserError as e:
        # Intentar sanitizar y reprocesar
        logger.warning(f"HTML malformado, intentando sanitizar: {str(e)}")
        try:
            sanitized_html = _sanitize_html(html)
            soup = BeautifulSoup(sanitized_html, 'html.parser')
        except Exception as e:
            # Si falla después de sanitizar, lanzar excepción
            error_fragment = html[:100] + "..." if len(html) > 100 else html
            raise MalformedHTMLError(
                f"No se pudo parsear el HTML: {str(e)}", 
                error_fragment
            )
    
    chunks = []
    
    # Función recursiva para procesar nodos
    def process_node(node, parent_path: Optional[str] = None):
        if isinstance(node, NavigableString):
            if node.strip() and len(node.strip()) >= min_text_length:
                if node.parent:
                    try:
                        path = _generate_css_path(node.parent)
                        is_rtl = _detect_rtl(node.parent)
                        chunks.append(TextChunk(
                            text=node.strip(),
                            path=path,
                            is_rtl=is_rtl
                        ))
                    except Exception as e:
                        # Si falla la generación del path, usar un path genérico
                        logger.warning(f"Error generando path CSS: {str(e)}")
                        chunks.append(TextChunk(
                            text=node.strip(),
                            path=f"body {node.parent.name}" if node.parent and node.parent.name else "body",
                            is_rtl=False
                        ))
        elif isinstance(node, Tag):
            # Procesar hijos
            for child in node.children:
                process_node(child)
    
    # Iniciar procesamiento
    process_node(soup)
    
    logger.debug(f"Extraídos {len(chunks)} fragmentos de texto")
    return chunks 