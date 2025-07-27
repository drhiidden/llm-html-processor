"""
Sistema de caché para respuestas de LLM.
"""

import hashlib
import json
import os
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from .base import ChatMessage

class LLMCache:
    """Cache para respuestas de LLM."""
    
    def __init__(
        self,
        cache_dir: str = ".llm_cache",
        ttl: int = 86400,  # 24 horas por defecto
        max_entries: int = 1000
    ):
        """
        Inicializa el sistema de caché.
        
        Args:
            cache_dir: Directorio para almacenar la caché
            ttl: Tiempo de vida de las entradas en segundos
            max_entries: Número máximo de entradas en caché
        """
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        self.max_entries = max_entries
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata: Dict[str, Dict[str, Any]] = self._load_metadata()
        
    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Carga los metadatos de la caché."""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_metadata(self) -> None:
        """Guarda los metadatos de la caché."""
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f)
        except IOError:
            pass  # Silenciar errores de escritura
    
    def _generate_key(self, messages: List[ChatMessage], model: str, params: Dict[str, Any]) -> str:
        """
        Genera una clave única para la consulta.
        
        Args:
            messages: Lista de mensajes
            model: Nombre del modelo
            params: Parámetros adicionales
            
        Returns:
            str: Clave hash para la consulta
        """
        # Normalizar mensajes para generar clave consistente
        msg_data = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        # Filtrar parámetros relevantes (ignorar timeout, etc.)
        relevant_params = {k: v for k, v in params.items() 
                          if k in ["temperature", "max_tokens", "top_p", "top_k"]}
        
        # Crear diccionario para hash
        hash_dict = {
            "messages": msg_data,
            "model": model,
            "params": relevant_params
        }
        
        # Generar hash
        hash_str = hashlib.sha256(json.dumps(hash_dict, sort_keys=True).encode()).hexdigest()
        return hash_str
    
    def get(
        self, 
        messages: List[ChatMessage], 
        model: str, 
        params: Dict[str, Any]
    ) -> Optional[str]:
        """
        Obtiene una respuesta de la caché si existe y es válida.
        
        Args:
            messages: Lista de mensajes
            model: Nombre del modelo
            params: Parámetros adicionales
            
        Returns:
            Optional[str]: Respuesta cacheada o None si no existe
        """
        key = self._generate_key(messages, model, params)
        
        # Verificar si existe en metadata
        if key not in self.metadata:
            return None
        
        # Verificar TTL
        entry = self.metadata[key]
        if time.time() - entry["timestamp"] > self.ttl:
            # Expirado, eliminar
            self._remove_entry(key)
            return None
        
        # Leer contenido
        cache_file = self.cache_dir / f"{key}.txt"
        if not cache_file.exists():
            self._remove_entry(key)
            return None
        
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return f.read()
        except IOError:
            self._remove_entry(key)
            return None
    
    def set(
        self, 
        messages: List[ChatMessage], 
        model: str, 
        params: Dict[str, Any], 
        response: str
    ) -> None:
        """
        Guarda una respuesta en la caché.
        
        Args:
            messages: Lista de mensajes
            model: Nombre del modelo
            params: Parámetros adicionales
            response: Respuesta a cachear
        """
        key = self._generate_key(messages, model, params)
        
        # Guardar contenido
        cache_file = self.cache_dir / f"{key}.txt"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(response)
        except IOError:
            return  # Silenciar errores de escritura
        
        # Actualizar metadata
        self.metadata[key] = {
            "timestamp": time.time(),
            "model": model,
            "params": {k: v for k, v in params.items() 
                      if k in ["temperature", "max_tokens", "top_p", "top_k"]}
        }
        
        # Limpiar caché si es necesario
        self._cleanup()
        
        # Guardar metadata
        self._save_metadata()
    
    def _remove_entry(self, key: str) -> None:
        """Elimina una entrada de la caché."""
        if key in self.metadata:
            del self.metadata[key]
        
        cache_file = self.cache_dir / f"{key}.txt"
        if cache_file.exists():
            try:
                os.remove(cache_file)
            except OSError:
                pass
    
    def _cleanup(self) -> None:
        """Limpia entradas antiguas si se excede el límite."""
        if len(self.metadata) <= self.max_entries:
            return
        
        # Ordenar por timestamp (más antiguo primero)
        sorted_entries = sorted(
            self.metadata.items(),
            key=lambda x: x[1]["timestamp"]
        )
        
        # Eliminar entradas más antiguas
        to_remove = len(self.metadata) - self.max_entries
        for key, _ in sorted_entries[:to_remove]:
            self._remove_entry(key)
    
    def clear(self) -> None:
        """Limpia toda la caché."""
        for key in list(self.metadata.keys()):
            self._remove_entry(key)
        self.metadata = {}
        self._save_metadata()

# Instancia global para uso en toda la aplicación
global_cache = LLMCache() 