"""
Módulo que define las excepciones personalizadas para el procesamiento LLM.
"""

class LLMError(Exception):
    """Excepción base para todos los errores relacionados con LLM."""
    pass

class RateLimitError(LLMError):
    """Se lanza cuando se excede el límite de tasa de la API."""
    pass

class AuthenticationError(LLMError):
    """Se lanza cuando hay un error de autenticación con la API."""
    pass

class ModelError(LLMError):
    """Se lanza cuando hay un error con el modelo LLM."""
    pass

class InvalidResponseError(LLMError):
    """Se lanza cuando la respuesta del modelo no es válida."""
    pass

class ConfigurationError(LLMError):
    """Se lanza cuando hay un error en la configuración del cliente LLM."""
    pass

class RetryError(LLMError):
    """Se lanza cuando se agotan los reintentos después de varios errores."""
    pass 