from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, TelField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp
from models import User

class RegistrationForm(FlaskForm):
    first_name = StringField('Prénom', validators=[
        DataRequired(message='Le prénom est requis'),
        Length(min=2, max=80, message='Le prénom doit contenir entre 2 et 80 caractères')
    ])
    
    last_name = StringField('Nom', validators=[
        DataRequired(message='Le nom est requis'),
        Length(min=2, max=80, message='Le nom doit contenir entre 2 et 80 caractères')
    ])
    
    email = EmailField('Email', validators=[
        DataRequired(message='L\'email est requis'),
        Email(message='Email invalide')
    ])
    
    phone = TelField('Téléphone WhatsApp', validators=[
        DataRequired(message='Le numéro de téléphone est requis'),
        Regexp(r'^(\+226|226|00226)?[0-9]{8}$', message='Numéro de téléphone Burkina Faso invalide (ex: +22670123456 ou 70123456)')
    ])
    
    password = PasswordField('Mot de passe', validators=[
        DataRequired(message='Le mot de passe est requis'),
        Length(min=8, message='Le mot de passe doit contenir au moins 8 caractères')
    ])
    
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(message='Veuillez confirmer votre mot de passe'),
        EqualTo('password', message='Les mots de passe ne correspondent pas')
    ])
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Cet email est déjà utilisé')
    
    def validate_phone(self, field):
        # Normaliser le numéro de téléphone
        phone = field.data
        if phone.startswith('00226'):
            phone = '+226' + phone[5:]
        elif phone.startswith('226'):
            phone = '+226' + phone[3:]
        elif len(phone) == 8 and phone.isdigit():
            phone = '+226' + phone
        
        if User.query.filter_by(phone=phone).first():
            raise ValidationError('Ce numéro de téléphone est déjà utilisé')


class LoginForm(FlaskForm):
    login = StringField('Email ou Téléphone', validators=[
        DataRequired(message='L\'email ou téléphone est requis')
    ])
    
    password = PasswordField('Mot de passe', validators=[
        DataRequired(message='Le mot de passe est requis')
    ])
    
    remember_me = BooleanField('Se souvenir de moi')


class EmailVerificationForm(FlaskForm):
    verification_code = StringField('Code de vérification', validators=[
        DataRequired(message='Le code de vérification est requis'),
        Length(min=6, max=6, message='Le code doit contenir exactement 6 chiffres'),
        Regexp(r'^\d{6}$', message='Le code doit contenir uniquement des chiffres')
    ])


class OTPVerificationForm(FlaskForm):
    otp_code = StringField('Code OTP WhatsApp', validators=[
        DataRequired(message='Le code OTP est requis'),
        Length(min=6, max=6, message='Le code doit contenir exactement 6 chiffres'),
        Regexp(r'^\d{6}$', message='Le code doit contenir uniquement des chiffres')
    ])


class ResetPasswordRequestForm(FlaskForm):
    email = EmailField('Email', validators=[
        DataRequired(message='L\'email est requis'),
        Email(message='Email invalide')
    ])


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nouveau mot de passe', validators=[
        DataRequired(message='Le mot de passe est requis'),
        Length(min=8, message='Le mot de passe doit contenir au moins 8 caractères')
    ])
    
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(message='Veuillez confirmer votre mot de passe'),
        EqualTo('password', message='Les mots de passe ne correspondent pas')
    ])


class ActivateAccountForm(FlaskForm):
    activation_token = StringField('Token d\'activation', validators=[
        DataRequired(message='Le token est requis'),
        Length(min=20, max=100)
    ])


class ProfileUpdateForm(FlaskForm):
    first_name = StringField('Prénom', validators=[
        DataRequired(message='Le prénom est requis'),
        Length(min=2, max=80)
    ])
    
    last_name = StringField('Nom', validators=[
        DataRequired(message='Le nom est requis'),
        Length(min=2, max=80)
    ])
    
    email = EmailField('Email', validators=[
        DataRequired(message='L\'email est requis'),
        Email(message='Email invalide')
    ])
    
    phone = TelField('Téléphone WhatsApp', validators=[
        DataRequired(message='Le numéro est requis'),
        Regexp(r'^(\+226|226|00226)?[0-9]{8}$', message='Numéro Burkina Faso invalide')
    ])
    
    def __init__(self, original_email, original_phone, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
        self.original_phone = original_phone
    
    def validate_email(self, field):
        if field.data.lower() != self.original_email:
            if User.query.filter_by(email=field.data.lower()).first():
                raise ValidationError('Cet email est déjà utilisé')
    
    def validate_phone(self, field):
        # Normaliser le numéro
        phone = field.data
        if phone.startswith('00226'):
            phone = '+226' + phone[5:]
        elif phone.startswith('226'):
            phone = '+226' + phone[3:]
        elif len(phone) == 8 and phone.isdigit():
            phone = '+226' + phone
        
        if phone != self.original_phone:
            if User.query.filter_by(phone=phone).first():
                raise ValidationError('Ce numéro est déjà utilisé')