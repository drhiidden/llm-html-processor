"""
Aplicación Flask para la interfaz web y API REST.
"""

import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, current_user
from werkzeug.middleware.proxy_fix import ProxyFix

from ..utils.logging import get_logger, LogConfig, setup_logging

logger = get_logger("web")

def create_app(test_config=None):
    """
    Crea y configura la aplicación Flask.
    
    Args:
        test_config: Configuración para pruebas (opcional)
        
    Returns:
        Flask: Aplicación Flask configurada
    """
    # Crear y configurar la app
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder='templates',
        static_folder='static'
    )
    
    # Configuración por defecto
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key-change-in-production'),
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,  # 10 MB máximo
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'uploads'),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
    )
    
    # Soporte para proxy
    app.wsgi_app = ProxyFix(app.wsgi_app)
    
    # Configuración de prueba si se proporciona
    if test_config is not None:
        app.config.from_mapping(test_config)
    
    # Configuración de producción
    if os.environ.get('FLASK_ENV') == 'production':
        app.config.from_pyfile('config.py', silent=True)
    
    # Asegurar que existe el directorio de instancia
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except OSError:
        pass
    
    # Inicializar CSRF
    csrf = CSRFProtect(app)
    
    # Inicializar Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    # Registrar blueprints
    from .routes.main import main_bp
    app.register_blueprint(main_bp)
    
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from .routes.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Cargar usuario para login_manager
    from .models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)
    
    # Filtros de Jinja
    @app.template_filter('datetime')
    def format_datetime(value):
        if not value:
            return ""
        dt = datetime.datetime.fromtimestamp(value)
        return dt.strftime('%d/%m/%Y %H:%M')
    
    # Ruta de prueba
    @app.route('/ping')
    def ping():
        return jsonify({"status": "ok", "message": "pong"})
    
    return app

def run_server():
    """
    Ejecuta el servidor de desarrollo.
    """
    # Configurar logging
    setup_logging(
        "web",
        LogConfig(level="DEBUG", console=True)
    )
    
    # Crear app
    app = create_app()
    
    # Ejecutar servidor
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    run_server() 