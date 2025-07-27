"""
Modelos para la aplicación web.
"""

import os
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from ..utils.logging import get_logger

logger = get_logger("web.models")

# Directorio para almacenar datos
DATA_DIR = os.environ.get("DATA_DIR", "instance/data")
os.makedirs(DATA_DIR, exist_ok=True)

# Planes de suscripción
class SubscriptionPlan:
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

# Configuración de planes
PLAN_CONFIG = {
    SubscriptionPlan.FREE: {
        "name": "Gratuito",
        "price": 0,
        "max_documents": 10,
        "max_size_kb": 50,
        "features": ["Procesamiento básico", "Modelos estándar"]
    },
    SubscriptionPlan.BASIC: {
        "name": "Básico",
        "price": 19,
        "max_documents": 100,
        "max_size_kb": 500,
        "features": ["Procesamiento avanzado", "Todos los modelos", "Estadísticas básicas"]
    },
    SubscriptionPlan.PRO: {
        "name": "Profesional",
        "price": 49,
        "max_documents": 500,
        "max_size_kb": 2048,  # 2MB
        "features": ["Procesamiento por lotes", "API REST", "Soporte prioritario", "Estadísticas avanzadas"]
    },
    SubscriptionPlan.ENTERPRISE: {
        "name": "Empresarial",
        "price": 199,
        "max_documents": -1,  # Ilimitado
        "max_size_kb": 10240,  # 10MB
        "features": ["Documentos ilimitados", "Tamaño personalizable", "API dedicada", "Soporte técnico 24/7"]
    }
}

@dataclass
class User(UserMixin):
    """Modelo de usuario."""
    id: str
    email: str
    name: str
    password_hash: str
    subscription_plan: str = SubscriptionPlan.FREE
    api_key: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    last_login: float = field(default_factory=time.time)
    documents_processed: int = 0
    total_tokens: int = 0
    
    @classmethod
    def create(cls, email: str, name: str, password: str) -> 'User':
        """
        Crea un nuevo usuario.
        
        Args:
            email: Email del usuario
            name: Nombre del usuario
            password: Contraseña en texto plano
            
        Returns:
            User: Usuario creado
        """
        user_id = str(uuid.uuid4())
        user = cls(
            id=user_id,
            email=email,
            name=name,
            password_hash=generate_password_hash(password)
        )
        user.save()
        return user
    
    def check_password(self, password: str) -> bool:
        """
        Verifica la contraseña del usuario.
        
        Args:
            password: Contraseña a verificar
            
        Returns:
            bool: True si la contraseña es correcta
        """
        return check_password_hash(self.password_hash, password)
    
    def update_login(self) -> None:
        """Actualiza la fecha de último login."""
        self.last_login = time.time()
        self.save()
    
    def get_plan_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración del plan de suscripción.
        
        Returns:
            Dict[str, Any]: Configuración del plan
        """
        return PLAN_CONFIG.get(self.subscription_plan, PLAN_CONFIG[SubscriptionPlan.FREE])
    
    def can_process_document(self, size_kb: float) -> bool:
        """
        Verifica si el usuario puede procesar un documento.
        
        Args:
            size_kb: Tamaño del documento en KB
            
        Returns:
            bool: True si puede procesar el documento
        """
        plan = self.get_plan_config()
        
        # Verificar tamaño máximo
        if size_kb > plan["max_size_kb"]:
            return False
        
        # Verificar límite de documentos
        max_docs = plan["max_documents"]
        if max_docs != -1 and self.documents_processed >= max_docs:
            return False
            
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el usuario a diccionario.
        
        Returns:
            Dict[str, Any]: Diccionario con los datos del usuario
        """
        data = asdict(self)
        # Eliminar datos sensibles
        data.pop("password_hash", None)
        return data
    
    def save(self) -> None:
        """Guarda el usuario en el almacenamiento."""
        users = User.load_all()
        users[self.id] = self
        
        users_data = {uid: user.to_dict() for uid, user in users.items()}
        
        try:
            with open(os.path.join(DATA_DIR, "users.json"), "w") as f:
                json.dump(users_data, f)
        except Exception as e:
            logger.error(f"Error al guardar usuario: {e}")
    
    @classmethod
    def get(cls, user_id: str) -> Optional['User']:
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Optional[User]: Usuario o None si no existe
        """
        users = cls.load_all()
        return users.get(user_id)
    
    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        """
        Obtiene un usuario por su email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Optional[User]: Usuario o None si no existe
        """
        users = cls.load_all()
        for user in users.values():
            if user.email == email:
                return user
        return None
    
    @classmethod
    def get_by_api_key(cls, api_key: str) -> Optional['User']:
        """
        Obtiene un usuario por su API key.
        
        Args:
            api_key: API key del usuario
            
        Returns:
            Optional[User]: Usuario o None si no existe
        """
        users = cls.load_all()
        for user in users.values():
            if user.api_key == api_key:
                return user
        return None
    
    @classmethod
    def load_all(cls) -> Dict[str, 'User']:
        """
        Carga todos los usuarios.
        
        Returns:
            Dict[str, User]: Diccionario de usuarios
        """
        try:
            with open(os.path.join(DATA_DIR, "users.json"), "r") as f:
                users_data = json.load(f)
                
            users = {}
            for uid, data in users_data.items():
                users[uid] = cls(**data)
            return users
        except FileNotFoundError:
            return {}
        except Exception as e:
            logger.error(f"Error al cargar usuarios: {e}")
            return {}

@dataclass
class ProcessedDocument:
    """Documento procesado."""
    id: str
    user_id: str
    original_html: str
    processed_html: str
    task: str
    model: str
    stats: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    
    @classmethod
    def create(
        cls, 
        user_id: str, 
        original_html: str, 
        processed_html: str, 
        task: str,
        model: str,
        stats: Dict[str, Any]
    ) -> 'ProcessedDocument':
        """
        Crea un nuevo documento procesado.
        
        Args:
            user_id: ID del usuario
            original_html: HTML original
            processed_html: HTML procesado
            task: Tarea realizada
            model: Modelo utilizado
            stats: Estadísticas de procesamiento
            
        Returns:
            ProcessedDocument: Documento procesado
        """
        doc_id = str(uuid.uuid4())
        doc = cls(
            id=doc_id,
            user_id=user_id,
            original_html=original_html,
            processed_html=processed_html,
            task=task,
            model=model,
            stats=stats
        )
        doc.save()
        
        # Actualizar estadísticas del usuario
        user = User.get(user_id)
        if user:
            user.documents_processed += 1
            user.total_tokens += stats.get("total_tokens_in", 0) + stats.get("total_tokens_out", 0)
            user.save()
            
        return doc
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el documento a diccionario.
        
        Returns:
            Dict[str, Any]: Diccionario con los datos del documento
        """
        data = asdict(self)
        return data
    
    def save(self) -> None:
        """Guarda el documento en el almacenamiento."""
        # Crear directorio para documentos del usuario si no existe
        user_dir = os.path.join(DATA_DIR, "documents", self.user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Guardar documento
        try:
            with open(os.path.join(user_dir, f"{self.id}.json"), "w") as f:
                json.dump(self.to_dict(), f)
        except Exception as e:
            logger.error(f"Error al guardar documento: {e}")
    
    @classmethod
    def get(cls, doc_id: str, user_id: str) -> Optional['ProcessedDocument']:
        """
        Obtiene un documento por su ID.
        
        Args:
            doc_id: ID del documento
            user_id: ID del usuario
            
        Returns:
            Optional[ProcessedDocument]: Documento o None si no existe
        """
        try:
            file_path = os.path.join(DATA_DIR, "documents", user_id, f"{doc_id}.json")
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, "r") as f:
                data = json.load(f)
                
            return cls(**data)
        except Exception as e:
            logger.error(f"Error al cargar documento: {e}")
            return None
    
    @classmethod
    def get_for_user(cls, user_id: str, limit: int = 10) -> List['ProcessedDocument']:
        """
        Obtiene los documentos de un usuario.
        
        Args:
            user_id: ID del usuario
            limit: Límite de documentos a obtener
            
        Returns:
            List[ProcessedDocument]: Lista de documentos
        """
        try:
            user_dir = os.path.join(DATA_DIR, "documents", user_id)
            if not os.path.exists(user_dir):
                return []
                
            docs = []
            for filename in os.listdir(user_dir)[:limit]:
                if filename.endswith(".json"):
                    with open(os.path.join(user_dir, filename), "r") as f:
                        data = json.load(f)
                        docs.append(cls(**data))
                        
            # Ordenar por fecha de creación (más recientes primero)
            docs.sort(key=lambda d: d.created_at, reverse=True)
            return docs
        except Exception as e:
            logger.error(f"Error al cargar documentos: {e}")
            return [] 