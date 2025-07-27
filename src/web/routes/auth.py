"""
Rutas de autenticación de la aplicación web.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from ..forms import LoginForm, RegisterForm, ProfileForm, PasswordChangeForm
from ..models import User
from ..utils import redirect_next

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Iniciar sesión."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            user.update_login()
            
            next_page = request.args.get('next')
            return redirect_next(next_page, 'main.dashboard')
            
        flash('Email o contraseña incorrectos', 'danger')
        
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registrar usuario."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = RegisterForm()
    
    if form.validate_on_submit():
        user = User.create(
            email=form.email.data,
            name=form.name.data,
            password=form.password.data
        )
        
        login_user(user)
        flash('¡Registro exitoso! Bienvenido/a.', 'success')
        return redirect(url_for('main.dashboard'))
        
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión."""
    logout_user()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Editar perfil."""
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Verificar si el email ya está en uso por otro usuario
        if form.email.data != current_user.email:
            existing_user = User.get_by_email(form.email.data)
            if existing_user:
                flash('Este email ya está en uso', 'danger')
                return render_template('auth/profile.html', form=form)
        
        # Actualizar datos
        current_user.name = form.name.data
        current_user.email = form.email.data
        current_user.save()
        
        flash('Perfil actualizado correctamente', 'success')
        return redirect(url_for('auth.profile'))
        
    return render_template('auth/profile.html', form=form)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Cambiar contraseña."""
    form = PasswordChangeForm()
    
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Contraseña actual incorrecta', 'danger')
            return render_template('auth/change_password.html', form=form)
            
        current_user.password_hash = generate_password_hash(form.new_password.data)
        current_user.save()
        
        flash('Contraseña actualizada correctamente', 'success')
        return redirect(url_for('auth.profile'))
        
    return render_template('auth/change_password.html', form=form)

@auth_bp.route('/regenerate-api-key', methods=['POST'])
@login_required
def regenerate_api_key():
    """Regenerar API key."""
    import uuid
    
    current_user.api_key = str(uuid.uuid4())
    current_user.save()
    
    flash('API key regenerada correctamente', 'success')
    return redirect(url_for('auth.profile')) 