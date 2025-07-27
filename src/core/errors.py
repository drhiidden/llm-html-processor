"""
Módulo para manejar errores específicos de HTML.
"""

class HTMLProcessingError(Exception):
    """Excepción base para errores de procesamiento HTML."""
    pass

class MalformedHTMLError(HTMLProcessingError):
    """Se lanza cuando el HTML está malformado."""
    
    def __init__(self, message: str, html_fragment: str = None):
        self.html_fragment = html_fragment
        super().__init__(message)

class EmptyHTMLError(HTMLProcessingError):
    """Se lanza cuando el HTML está vacío."""
    pass

class HTMLTooLargeError(HTMLProcessingError):
    """Se lanza cuando el HTML es demasiado grande para procesar."""
    
    def __init__(self, message: str, size_bytes: int, max_size_bytes: int):
        self.size_bytes = size_bytes
        self.max_size_bytes = max_size_bytes
        super().__init__(message)

class NodeNotFoundError(HTMLProcessingError):
    """Se lanza cuando no se puede encontrar un nodo por su path."""
    
    def __init__(self, message: str, path: str):
        self.path = path
        super().__init__(message)

class InvalidSelectorError(HTMLProcessingError):
    """Se lanza cuando un selector CSS es inválido."""
    
    def __init__(self, message: str, selector: str):
        self.selector = selector
        super().__init__(message) 