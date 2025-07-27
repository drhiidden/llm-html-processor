"""
Formularios para la aplicación web.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

from .models import User

class LoginForm(FlaskForm):
    """Formulario de login."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Recordarme')
    submit = SubmitField('Iniciar sesión')

class RegisterForm(FlaskForm):
    """Formulario de registro."""
    name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[
        DataRequired(), 
        Length(min=8, message="La contraseña debe tener al menos 8 caracteres")
    ])
    confirm = PasswordField('Confirmar contraseña', validators=[
        DataRequired(), 
        EqualTo('password', message="Las contraseñas deben coincidir")
    ])
    submit = SubmitField('Registrarse')
    
    def validate_email(self, field):
        """Valida que el email no esté ya registrado."""
        user = User.get_by_email(field.data)
        if user:
            raise ValidationError('Este email ya está registrado')

class HTMLProcessForm(FlaskForm):
    """Formulario para procesar HTML."""
    html_file = FileField('Archivo HTML', validators=[
        FileAllowed(['html', 'htm'], 'Solo se permiten archivos HTML')
    ])
    html_text = TextAreaField('O pega tu HTML aquí')
    task = SelectField('Tarea', choices=[
        ('paraphrase', 'Reescribir'),
        ('summarize', 'Resumir'),
        ('custom', 'Personalizado')
    ])
    language = StringField('Idioma', validators=[DataRequired()], default='he')
    model = SelectField('Modelo', choices=[
        ('gpt-4o-mini', 'GPT-4o Mini'),
        ('gpt-4o', 'GPT-4o'),
        ('gemini-pro', 'Gemini Pro'),
        ('llama2', 'Llama 2 (Local)')
    ])
    custom_prompt = TextAreaField('Prompt personalizado (solo para tarea personalizada)')
    use_cache = BooleanField('Usar caché', default=True)
    submit = SubmitField('Procesar')
    
    def validate(self):
        """Valida que se haya proporcionado HTML."""
        if not super().validate():
            return False
            
        if not self.html_file.data and not self.html_text.data:
            self.html_text.errors = ['Debes proporcionar un archivo HTML o pegar el HTML']
            return False
            
        if self.task.data == 'custom' and not self.custom_prompt.data:
            self.custom_prompt.errors = ['Debes proporcionar un prompt personalizado']
            return False
            
        return True

class ProfileForm(FlaskForm):
    """Formulario para editar perfil."""
    name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Guardar cambios')

class PasswordChangeForm(FlaskForm):
    """Formulario para cambiar contraseña."""
    current_password = PasswordField('Contraseña actual', validators=[DataRequired()])
    new_password = PasswordField('Nueva contraseña', validators=[
        DataRequired(), 
        Length(min=8, message="La contraseña debe tener al menos 8 caracteres")
    ])
    confirm = PasswordField('Confirmar nueva contraseña', validators=[
        DataRequired(), 
        EqualTo('new_password', message="Las contraseñas deben coincidir")
    ])
    submit = SubmitField('Cambiar contraseña') 