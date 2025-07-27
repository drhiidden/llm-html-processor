"""
Rutas principales de la aplicación web.
"""

import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from ...models import ProcessingOptions
from ...pipeline import process_html
from ..forms import HTMLProcessForm
from ..models import ProcessedDocument

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Página principal."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard del usuario."""
    # Obtener documentos recientes
    documents = ProcessedDocument.get_for_user(current_user.id, limit=5)
    
    # Obtener estadísticas
    stats = {
        "documents_processed": current_user.documents_processed,
        "total_tokens": current_user.total_tokens,
        "plan": current_user.get_plan_config()
    }
    
    return render_template(
        'dashboard.html', 
        documents=documents, 
        stats=stats
    )

@main_bp.route('/process', methods=['GET', 'POST'])
@login_required
def process():
    """Procesar HTML."""
    form = HTMLProcessForm()
    
    if form.validate_on_submit():
        # Obtener HTML
        html_content = ""
        if form.html_file.data:
            # Guardar archivo temporalmente
            filename = secure_filename(form.html_file.data.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            form.html_file.data.save(filepath)
            
            # Leer contenido
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            # Eliminar archivo temporal
            os.remove(filepath)
        else:
            html_content = form.html_text.data
        
        # Verificar límites del plan
        size_kb = len(html_content) / 1024
        if not current_user.can_process_document(size_kb):
            flash('Has excedido los límites de tu plan de suscripción', 'danger')
            return render_template('process.html', form=form)
        
        # Crear opciones de procesamiento
        options = ProcessingOptions(
            task=form.task.data,
            language=form.language.data,
            model=form.model.data,
            extra_prompt=form.custom_prompt.data if form.task.data == 'custom' else None,
            use_cache=form.use_cache.data
        )
        
        try:
            # Procesar HTML
            result = process_html(html_content, options)
            
            # Guardar documento procesado
            doc = ProcessedDocument.create(
                user_id=current_user.id,
                original_html=html_content,
                processed_html=result.html,
                task=options.task,
                model=options.model,
                stats=result.stats
            )
            
            # Redireccionar a resultados
            return redirect(url_for('main.result', doc_id=doc.id))
            
        except Exception as e:
            flash(f'Error al procesar HTML: {str(e)}', 'danger')
    
    return render_template('process.html', form=form)

@main_bp.route('/result/<doc_id>')
@login_required
def result(doc_id):
    """Ver resultado de procesamiento."""
    # Obtener documento
    doc = ProcessedDocument.get(doc_id, current_user.id)
    if not doc:
        flash('Documento no encontrado', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('result.html', doc=doc)

@main_bp.route('/documents')
@login_required
def documents():
    """Ver documentos procesados."""
    # Obtener documentos
    documents = ProcessedDocument.get_for_user(current_user.id, limit=50)
    
    return render_template('documents.html', documents=documents)

@main_bp.route('/plans')
def plans():
    """Ver planes de suscripción."""
    from ..models import PLAN_CONFIG, SubscriptionPlan
    
    plans = [
        {
            "id": SubscriptionPlan.FREE,
            "config": PLAN_CONFIG[SubscriptionPlan.FREE]
        },
        {
            "id": SubscriptionPlan.BASIC,
            "config": PLAN_CONFIG[SubscriptionPlan.BASIC]
        },
        {
            "id": SubscriptionPlan.PRO,
            "config": PLAN_CONFIG[SubscriptionPlan.PRO]
        },
        {
            "id": SubscriptionPlan.ENTERPRISE,
            "config": PLAN_CONFIG[SubscriptionPlan.ENTERPRISE]
        }
    ]
    
    return render_template('plans.html', plans=plans) 