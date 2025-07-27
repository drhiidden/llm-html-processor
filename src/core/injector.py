"""
Inyector de texto en documentos HTML.
"""

from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Optional, Set
from ..models import TextChunk
from .errors import MalformedHTMLError, NodeNotFoundError, InvalidSelectorError
from ..utils.logging import get_logger

logger = get_logger("injector")

def _find_node_by_path(soup: BeautifulSoup, path: str) -> Optional[Tag]:
    """
    Busca un nodo en el HTML usando un path CSS.
    
    Args:
        soup: Objeto BeautifulSoup
        path: Path CSS para buscar
        
    Returns:
        Optional[Tag]: Nodo encontrado o None
        
    Raises:
        InvalidSelectorError: Si el selector CSS es inválido
    """
    try:
        # Intentar seleccionar directamente
        nodes = soup.select(path)
        if nodes:
            return nodes[0]
            
        # Si no funciona, intentar una búsqueda más flexible
        parts = path.split(" > ")
        if not parts:
            return None
            
        # Buscar por el último componente del path
        last_part = parts[-1]
        candidates = soup.select(last_part)
        
        # Si hay múltiples candidatos, intentar refinar con partes anteriores del path
        if len(candidates) > 1 and len(parts) > 1:
            for candidate in candidates:
                # Reconstruir path desde el candidato y comparar
                current = candidate
                path_parts = [last_part]
                
                for _ in range(len(parts) - 1):
                    if not current.parent:
                        break
                    current = current.parent
                    # Simplificar para comparación (solo nombre de tag)
                    path_parts.append(current.name)
                
                # Comparar paths simplificados
                original_simple = [p.split("#")[0].split(".")[0].split(":")[0] for p in reversed(parts)]
                candidate_simple = [p.split("#")[0].split(".")[0].split(":")[0] for p in path_parts]
                
                if len(original_simple) <= len(candidate_simple) and all(
                    a == b for a, b in zip(original_simple, candidate_simple[:len(original_simple)])
                ):
                    return candidate
                    
        # Si hay un solo candidato, devolverlo
        if len(candidates) == 1:
            return candidates[0]
            
        return None
    except Exception as e:
        raise InvalidSelectorError(f"Selector CSS inválido '{path}': {str(e)}", path)

def _validate_chunks(chunks: List[TextChunk]) -> None:
    """
    Valida la lista de chunks.
    
    Args:
        chunks: Lista de chunks a validar
        
    Raises:
        ValueError: Si la lista está vacía o contiene chunks inválidos
    """
    if not chunks:
        raise ValueError("La lista de chunks está vacía")
    
    for i, chunk in enumerate(chunks):
        if not chunk.path:
            raise ValueError(f"El chunk {i} no tiene path")
        if chunk.text is None:  # Permitir texto vacío, pero no None
            raise ValueError(f"El chunk {i} tiene texto None")

def inject_text(html: str, chunks: List[TextChunk], strict: bool = False) -> str:
    """
    Inyecta texto procesado de vuelta en el HTML.
    
    Args:
        html: HTML original como string
        chunks: Lista de fragmentos de texto procesados
        strict: Si es True, lanza excepciones cuando no se encuentra un nodo
        
    Returns:
        str: HTML con el texto inyectado
        
    Raises:
        MalformedHTMLError: Si el HTML está malformado
        NodeNotFoundError: Si no se encuentra un nodo y strict=True
    """
    # Validar chunks
    _validate_chunks(chunks)
    
    # Parsear HTML
    try:
        soup = BeautifulSoup(html, 'html.parser')
    except Exception as e:
        raise MalformedHTMLError(f"Error al parsear HTML: {str(e)}")
    
    # Crear un mapa de paths a chunks para acceso más rápido
    chunk_map: Dict[str, TextChunk] = {chunk.path: chunk for chunk in chunks}
    
    # Mapa para rastrear nodos ya procesados
    processed_nodes: Set[str] = set()
    
    # Contador de errores
    errors = 0
    
    # Primero intentar inyección directa por path
    for path, chunk in chunk_map.items():
        try:
            node = _find_node_by_path(soup, path)
            if node:
                # Verificar si el nodo tiene contenido de texto directo
                for child in node.children:
                    if child.string and child.string.strip():
                        child.replace_with(chunk.text)
                        processed_nodes.add(path)
                        logger.debug(f"Inyectado texto en nodo: {path}")
                        break
                
                # Si no tenía texto directo, establecer el contenido completo
                if path not in processed_nodes:
                    node.string = chunk.text
                    processed_nodes.add(path)
                    logger.debug(f"Establecido texto en nodo: {path}")
            elif strict:
                raise NodeNotFoundError(f"No se encontró el nodo con path: {path}", path)
            else:
                logger.warning(f"No se encontró el nodo con path: {path}")
                errors += 1
        except InvalidSelectorError as e:
            logger.warning(f"Selector inválido: {e}")
            errors += 1
            if strict:
                raise
    
    # Para los chunks no procesados, hacer una búsqueda por contenido
    unprocessed = [chunk for chunk in chunks if chunk.path not in processed_nodes]
    if unprocessed:
        logger.debug(f"Intentando inyectar {len(unprocessed)} chunks no procesados")
        for node in soup.find_all(text=True):
            if node.strip():
                for chunk in unprocessed:
                    # Buscar coincidencia aproximada
                    if node.strip() in chunk.path or chunk.path in node.strip():
                        node.replace_with(chunk.text)
                        logger.debug(f"Inyectado texto por coincidencia aproximada: {chunk.path}")
                        break
    
    if errors > 0:
        logger.warning(f"No se pudieron inyectar {errors} chunks")
    
    return str(soup) 