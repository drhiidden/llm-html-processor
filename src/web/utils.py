"""
Utilidades para la aplicación web.
"""

from urllib.parse import urlparse
from flask import url_for, redirect

def is_safe_url(target):
    """
    Verifica si una URL es segura para redireccionar.
    
    Args:
        target: URL a verificar
        
    Returns:
        bool: True si es segura
    """
    ref_url = urlparse(target)
    return not ref_url.netloc and ref_url.scheme == ''

def redirect_next(target, default):
    """
    Redirecciona a la URL objetivo si es segura, o a la URL por defecto.
    
    Args:
        target: URL objetivo
        default: URL por defecto
        
    Returns:
        Response: Respuesta de redirección
    """
    if target and is_safe_url(target):
        return redirect(target)
    return redirect(url_for(default)) 