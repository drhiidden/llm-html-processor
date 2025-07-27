"""
Rutas de la API REST.
"""

import functools
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden

from ...models import ProcessingOptions
from ...pipeline import process_html
from ..models import User, ProcessedDocument

api_bp = Blueprint('api', __name__)

def require_api_key(f):
    """Decorador para requerir API key."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "API key is required"}), 401
            
        user = User.get_by_api_key(api_key)
        if not user:
            return jsonify({"error": "Invalid API key"}), 401
            
        # Verificar si el plan permite uso de API
        plan = user.get_plan_config()
        if user.subscription_plan == "free" or user.subscription_plan == "basic":
            return jsonify({"error": "Your subscription plan does not include API access"}), 403
            
        # Pasar el usuario a la función
        return f(user, *args, **kwargs)
    return decorated

@api_bp.route('/ping', methods=['GET'])
def ping():
    """Endpoint de prueba."""
    return jsonify({"status": "ok", "message": "pong"})

@api_bp.route('/process', methods=['POST'])
@require_api_key
def process_html_api(user):
    """Procesar HTML vía API."""
    try:
        # Obtener datos
        data = request.json
        if not data:
            raise BadRequest("No JSON data provided")
            
        # Validar HTML
        html_content = data.get('html')
        if not html_content:
            raise BadRequest("HTML content is required")
            
        # Verificar límites del plan
        size_kb = len(html_content) / 1024
        if not user.can_process_document(size_kb):
            raise Forbidden("You have exceeded your subscription plan limits")
            
        # Obtener opciones
        task = data.get('task', 'paraphrase')
        language = data.get('language', 'he')
        model = data.get('model', 'gpt-4o-mini')
        extra_prompt = data.get('prompt')
        use_cache = data.get('use_cache', True)
        
        # Validar opciones
        if task not in ['paraphrase', 'summarize', 'custom']:
            raise BadRequest("Invalid task")
            
        if task == 'custom' and not extra_prompt:
            raise BadRequest("Custom prompt is required for custom task")
            
        # Crear opciones de procesamiento
        options = ProcessingOptions(
            task=task,
            language=language,
            model=model,
            extra_prompt=extra_prompt,
            use_cache=use_cache
        )
        
        # Procesar HTML
        result = process_html(html_content, options)
        
        # Guardar documento procesado
        doc = ProcessedDocument.create(
            user_id=user.id,
            original_html=html_content,
            processed_html=result.html,
            task=options.task,
            model=options.model,
            stats=result.stats
        )
        
        # Devolver resultado
        return jsonify({
            "id": doc.id,
            "html": result.html,
            "stats": result.stats
        })
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Forbidden as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        current_app.logger.error(f"API error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route('/documents', methods=['GET'])
@require_api_key
def get_documents(user):
    """Obtener documentos procesados."""
    try:
        # Obtener parámetros
        limit = request.args.get('limit', 10, type=int)
        if limit > 50:
            limit = 50
            
        # Obtener documentos
        documents = ProcessedDocument.get_for_user(user.id, limit=limit)
        
        # Preparar respuesta
        docs_data = []
        for doc in documents:
            docs_data.append({
                "id": doc.id,
                "task": doc.task,
                "model": doc.model,
                "created_at": doc.created_at,
                "stats": doc.stats
            })
            
        return jsonify({
            "documents": docs_data,
            "count": len(docs_data)
        })
        
    except Exception as e:
        current_app.logger.error(f"API error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route('/documents/<doc_id>', methods=['GET'])
@require_api_key
def get_document(user, doc_id):
    """Obtener un documento procesado."""
    try:
        # Obtener documento
        doc = ProcessedDocument.get(doc_id, user.id)
        if not doc:
            return jsonify({"error": "Document not found"}), 404
            
        # Preparar respuesta
        doc_data = {
            "id": doc.id,
            "task": doc.task,
            "model": doc.model,
            "created_at": doc.created_at,
            "stats": doc.stats,
            "original_html": doc.original_html,
            "processed_html": doc.processed_html
        }
            
        return jsonify(doc_data)
        
    except Exception as e:
        current_app.logger.error(f"API error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500 