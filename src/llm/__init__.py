"""
Módulo principal para el procesamiento de HTML con LLMs.
"""

from .openai_client import OpenAIClient
from .gemini_client import GeminiClient
from .local_client import LocalClient
from .errors import (
    LLMError,
    RateLimitError,
    AuthenticationError,
    ModelError,
    InvalidResponseError,
    ConfigurationError,
    RetryError
)

__all__ = [
    'OpenAIClient',
    'GeminiClient',
    'LocalClient',
    'LLMError',
    'RateLimitError',
    'AuthenticationError',
    'ModelError',
    'InvalidResponseError',
    'ConfigurationError',
    'RetryError'
] 