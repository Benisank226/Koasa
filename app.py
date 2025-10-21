import os
from dotenv import load_dotenv

# Chargement basique de l'environnement
if os.path.exists('.env.production'):
    load_dotenv('.env.production')
    print("🔧 .env.production chargé")
else:
    load_dotenv('.env')
    print("🔧 .env chargé")

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import os
import secrets
from sqlalchemy.orm import joinedload

from models import db, User, Product, Order, OrderItem, Category
from forms import (
    RegistrationForm, LoginForm, ProfileUpdateForm, 
    EmailVerificationForm, OTPVerificationForm,
    ResetPasswordRequestForm, ResetPasswordForm, ActivateAccountForm
)
from utils import (
    send_verification_email, send_activation_whatsapp,
    send_order_confirmation_whatsapp, generate_invoice_pdf,
    send_password_reset_email, generate_order_whatsapp_link,
    send_activation_confirmation_whatsapp, send_otp_whatsapp
)
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# ✅ DÉTECTION INTELLIGENTE POSTGRESQL RAILWAY
print("=" * 50)
print("🔍 DIAGNOSTIC BASE DE DONNÉES RAILWAY")
print("=" * 50)

# Méthode 1: DATABASE_URL directe
database_url = os.environ.get('DATABASE_URL')

# Méthode 2: Variables PostgreSQL individuelles
pg_host = os.environ.get('PGHOST')
pg_user = os.environ.get('PGUSER')
pg_password = os.environ.get('PGPASSWORD')
pg_database = os.environ.get('PGDATABASE')
pg_port = os.environ.get('PGPORT', '5432')

print(f"DATABASE_URL: {'✅ PRÉSENTE' if database_url else '❌ ABSENTE'}")
print(f"PGHOST: {pg_host or '❌ NON DÉFINI'}")
print(f"PGDATABASE: {pg_database or '❌ NON DÉFINI'}")

if database_url and database_url.startswith('postgres'):
    # PostgreSQL Railway détecté via DATABASE_URL
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        print("🔄 Conversion postgres:// → postgresql://")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print("🎯 POSTGRESQL CONFIGURÉ (DATABASE_URL)")
    print(f"🔗 Base: {database_url.split('@')[-1] if '@' in database_url else 'URL masquée'}")

elif pg_host and pg_user and pg_password and pg_database:
    # Construction URL depuis variables individuelles
    database_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print("🎯 POSTGRESQL CONFIGURÉ (VARIABLES INDIVIDUELLES)")
    print(f"🔗 Hôte: {pg_host}, Base: {pg_database}")

else:
    # Fallback SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///koasa.db'
    print("🔧 SQLITE (DÉVELOPPEMENT LOCAL)")

print("=" * 50)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True
}

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Normalisation des numéros de téléphone
def normalize_phone(phone):
    """Normalise le numéro de téléphone au format +226XXXXXXXX"""
    phone = "".join(filter(str.isdigit, phone))
    
    if phone.startswith('00226'):
        return '+' + phone[2:]
    elif phone.startswith('226'):
        return '+' + phone
    elif len(phone) == 8 and phone.isdigit():
        return '+226' + phone
        
    return phone if phone.startswith('+') else phone

# Routes existantes (inchangées)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            normalized_phone = normalize_phone(form.phone.data)
            
            user = User(
                email=form.email.data.lower(),
                phone=normalized_phone,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                is_active=True
            )
            user.set_password(form.password.data)
            
            # ✅ VÉRIFICATION WHATSAPP SEULEMENT
            user.email_verified = True  # Email auto-validé
            user.generate_activation_token()  # Token WhatsApp
            
            db.session.add(user)
            db.session.commit()
            
            # ✅ REDIRECTION VERS VÉRIFICATION WHATSAPP
            flash('✅ Inscription réussie! Vérifiez votre WhatsApp pour activer votre compte.', 'success')
            return redirect(url_for('verify_whatsapp_now', user_id=user.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'inscription: {str(e)}', 'danger')
    
    return render_template('register.html', form=form)

@app.route('/verify-email/<int:user_id>', methods=['GET', 'POST'])
def verify_email(user_id):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    if user.email_verified:
        flash('Votre email est déjà vérifié.', 'info')
        return redirect(url_for('post_activation', user_id=user.id))
    
    form = EmailVerificationForm()
    
    if form.validate_on_submit():
        if user.verify_email_code(form.verification_code.data):
            db.session.commit()
            flash('✅ Email vérifié avec succès!', 'success')
            return redirect(url_for('post_activation', user_id=user.id))
        else:
            flash('❌ Code invalide ou expiré. Veuillez réessayer.', 'danger')
    
    if user.email_code_expires and datetime.now(timezone.utc) > user.email_code_expires.replace(tzinfo=timezone.utc):
        flash('⚠️ Le code de vérification a expiré. Un nouveau code a été envoyé.', 'warning')
        user.generate_email_verification_code()
        db.session.commit()
        send_verification_email(user, user.email_verification_code)
    
    return render_template('verify_email.html', form=form, user=user)

@app.route('/resend-verification/<int:user_id>')
def resend_verification(user_id):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    if user.email_verified:
        flash('Votre email est déjà vérifié.', 'info')
        return redirect(url_for('login'))
    
    verification_code = user.generate_email_verification_code()
    db.session.commit()
    
    send_verification_email(user, verification_code)
    flash('✅ Nouveau code de vérification envoyé à votre email.', 'success')
    return redirect(url_for('verify_email', user_id=user.id))

@app.route('/post-activation/<int:user_id>')
def post_activation(user_id):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    if not user.email_verified:
        flash('Veuillez d\'abord vérifier votre email.', 'warning')
        return redirect(url_for('verify_email', user_id=user.id))
    
    return render_template('post_activation.html', user=user)

@app.route('/verify-whatsapp-now/<int:user_id>')
def verify_whatsapp_now(user_id):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    if not user.email_verified:
        flash('Veuillez d\'abord vérifier votre email.', 'warning')
        return redirect(url_for('verify_email', user_id=user.id))
    
    whatsapp_url = send_activation_whatsapp(user)
    
    flash('✅ WhatsApp ouvert! Envoyez votre token à l\'admin pour activer votre compte.', 'success')
    return render_template('send_whatsapp.html', 
                         whatsapp_url=whatsapp_url, 
                         user=user,
                         token=user.activation_token)

@app.route('/activate', methods=['POST'])
def activate_account():
    form = ActivateAccountForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(activation_token=form.activation_token.data).first()
        
        if user:
            user.whatsapp_verified = True
            db.session.commit()
            
            send_activation_confirmation_whatsapp(user)
            
            flash('✅ Compte activé avec succès! Votre WhatsApp est maintenant vérifié.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Token d\'activation invalide.', 'danger')
    
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    activate_form = ActivateAccountForm()
    
    if form.validate_on_submit():
        login_input = form.login.data.lower()
        password = form.password.data
        
        user = User.query.filter(
            (User.email == login_input) | 
            (User.phone == normalize_phone(login_input))
        ).first()
        
        if user:
            # ✅ VÉRIFICATION WHATSAPP OBLIGATOIRE
            if not user.whatsapp_verified:
                flash('⚠️ Veuillez vérifier votre WhatsApp avant de vous connecter.', 'warning')
                return redirect(url_for('verify_whatsapp_now', user_id=user.id))
            
            if user.check_password(password):
                login_user(user, remember=form.remember_me.data)
                flash(f'Bienvenue {user.first_name}!', 'success')
                
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Email/téléphone ou mot de passe incorrect.', 'danger')
        else:
            flash('Email/téléphone ou mot de passe incorrect.', 'danger')
    
    return render_template('login.html', form=form, activate_form=activate_form)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = ResetPasswordRequestForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user:
            reset_token = secrets.token_urlsafe(32)
            user.reset_token = reset_token
            user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
            db.session.commit()
            
            send_password_reset_email(user, reset_token)
        
        flash('✅ Si cet email existe, un lien de réinitialisation a été envoyé.', 'success')
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user = User.query.filter_by(reset_token=token).first()
    
    is_expired = False
    if user and user.reset_token_expires:
        if datetime.now(timezone.utc) > user.reset_token_expires.replace(tzinfo=timezone.utc):
            is_expired = True

    if not user or is_expired:
        flash('Lien de réinitialisation invalide ou expiré.', 'danger')
        return redirect(url_for('forgot_password'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        
        flash('✅ Mot de passe réinitialisé avec succès! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', form=form, token=token)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Déconnexion réussie. À bientôt! 👋', 'info')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileUpdateForm(
        original_email=current_user.email,
        original_phone=current_user.phone,
        obj=current_user
    )
    
    if form.validate_on_submit():
        try:
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.email = form.email.data.lower()
            
            new_phone = normalize_phone(form.phone.data)
            if current_user.phone != new_phone:
                current_user.phone = new_phone
                current_user.whatsapp_verified = False
                flash('⚠️ Numéro modifié. Veuillez vérifier votre nouveau WhatsApp.', 'warning')
            
            db.session.commit()
            flash('✅ Profil mis à jour avec succès!', 'success')
            return redirect(url_for('profile'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    return render_template('profile.html', form=form, orders=orders)

@app.route('/profile/generate-whatsapp-token', methods=['POST'])
@login_required
def generate_whatsapp_token():
    try:
        current_user.generate_activation_token()
        db.session.commit()
        
        whatsapp_url = send_activation_whatsapp(current_user)
        
        return jsonify({
            'success': True,
            'message': '✅ Token généré! WhatsApp ouvert.',
            'whatsapp_url': whatsapp_url,
            'token': current_user.activation_token
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'❌ Erreur: {str(e)}'
        }), 500

# --- ROUTES ADMIN ---

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('index'))
    
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        users = User.query.filter(
            db.or_(
                User.id == int(search_query) if search_query.isdigit() else False,
                User.email.ilike(f'%{search_query}%'),
                User.phone.ilike(f'%{search_query}%'),
                User.first_name.ilike(f'%{search_query}%'),
                User.last_name.ilike(f'%{search_query}%'),
                User.activation_token == search_query
            )
        ).all()
    else:
        users = User.query.order_by(User.created_at.desc()).all()
    
    return render_template('admin_users.html', users=users, search_query=search_query)

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('index'))

    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')

    query = Order.query.options(joinedload(Order.customer))
    
    if search_query:
        query = query.join(User).filter(
            db.or_(
                Order.whatsapp_order_id.ilike(f'%{search_query}%'),
                Order.order_number.ilike(f'%{search_query}%'),
                User.first_name.ilike(f'%{search_query}%'),
                User.last_name.ilike(f'%{search_query}%'),
                User.phone.ilike(f'%{search_query}%')
            )
        )
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    total_orders = len(orders)
    total_sales = sum(order.total_amount for order in orders)
    pending_orders = sum(1 for order in orders if order.status == 'en_attente')
    confirmed_orders = sum(1 for order in orders if order.status == 'confirme')
    preparation_orders = sum(1 for order in orders if order.status == 'preparation')
    delivered_orders = sum(1 for order in orders if order.status == 'livree')
    
    stats = {
        'total': total_orders,
        'en_attente': pending_orders,
        'confirme': confirmed_orders,
        'preparation': preparation_orders,
        'livree': delivered_orders,
        'total_sales': total_sales
    }

    return render_template('admin_orders.html', 
                         orders=orders, 
                         stats=stats,
                         search_query=search_query,
                         status_filter=status_filter)

# --- ROUTES ADMIN PRODUITS ---

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('index'))
    
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '')
    availability_filter = request.args.get('availability', '')
    
    # Construction de la requête
    query = Product.query.options(joinedload(Product.category_ref))
    
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))
    
    if category_filter:
        query = query.filter(Product.category_id == int(category_filter))
    
    if availability_filter:
        if availability_filter == 'available':
            query = query.filter(Product.is_available == True)
        elif availability_filter == 'unavailable':
            query = query.filter(Product.is_available == False)
    
    products = query.order_by(Product.created_at.desc()).all()
    categories = Category.query.filter_by(is_active=True).all()
    
    # Statistiques
    total_products = len(products)
    available_products = sum(1 for p in products if p.is_available)
    unavailable_products = total_products - available_products
    
    stats = {
        'total': total_products,
        'available': available_products,
        'unavailable': unavailable_products
    }
    
    return render_template('admin_products.html', 
                         products=products, 
                         categories=categories,
                         stats=stats,
                         search_query=search_query,
                         category_filter=category_filter,
                         availability_filter=availability_filter)

@app.route('/admin/categories')
@login_required
def admin_categories():
    if not current_user.is_admin:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('index'))
    
    categories = Category.query.order_by(Category.name).all()
    
    # Statistiques
    total_categories = len(categories)
    active_categories = sum(1 for c in categories if c.is_active)
    
    stats = {
        'total': total_categories,
        'active': active_categories
    }
    
    return render_template('admin_categories.html', 
                         categories=categories,
                         stats=stats)

# API Routes pour produits
@app.route('/admin/api/products', methods=['POST'])
@login_required
def api_create_product():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    data = request.json
    
    try:
        # Validation des données
        if not data.get('name') or not data.get('price') or not data.get('category_id'):
            return jsonify({'success': False, 'message': 'Données manquantes'}), 400
        
        # Vérifier que la catégorie existe
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({'success': False, 'message': 'Catégorie invalide'}), 400
        
        product = Product(
            name=data['name'],
            description=data.get('description', ''),
            price=float(data['price']),
            unit=data.get('unit', 'kg'),
            category_id=data['category_id'],
            image_url=data.get('image_url', ''),
            stock=int(data.get('stock', 0)),
            is_available=bool(data.get('is_available', True))
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '✅ Produit créé avec succès!',
            'product': product.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/admin/api/products/<int:product_id>', methods=['PUT'])
@login_required
def api_update_product(product_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    product = Product.query.get_or_404(product_id)
    data = request.json
    
    try:
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = float(data['price'])
        if 'unit' in data:
            product.unit = data['unit']
        if 'category_id' in data:
            category = Category.query.get(data['category_id'])
            if not category:
                return jsonify({'success': False, 'message': 'Catégorie invalide'}), 400
            product.category_id = data['category_id']
        if 'image_url' in data:
            product.image_url = data['image_url']
        if 'stock' in data:
            product.stock = int(data['stock'])
        if 'is_available' in data:
            product.is_available = bool(data['is_available'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '✅ Produit mis à jour avec succès!',
            'product': product.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/admin/api/products/<int:product_id>', methods=['DELETE'])
@login_required
def api_delete_product(product_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    product = Product.query.get_or_404(product_id)
    
    try:
        # Vérifier si le produit est utilisé dans des commandes
        if product.order_items:
            return jsonify({
                'success': False, 
                'message': '❌ Impossible de supprimer: produit utilisé dans des commandes'
            }), 400
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '✅ Produit supprimé avec succès!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

# API Routes pour catégories
@app.route('/admin/api/categories', methods=['POST'])
@login_required
def api_create_category():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    data = request.json
    
    try:
        if not data.get('name'):
            return jsonify({'success': False, 'message': 'Nom de catégorie manquant'}), 400
        
        # Vérifier si la catégorie existe déjà
        existing_category = Category.query.filter_by(name=data['name']).first()
        if existing_category:
            return jsonify({'success': False, 'message': 'Cette catégorie existe déjà'}), 400
        
        category = Category(
            name=data['name'],
            description=data.get('description', ''),
            icon=data.get('icon', 'fas fa-cube')
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '✅ Catégorie créée avec succès!',
            'category': category.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/admin/api/categories/<int:category_id>', methods=['PUT'])
@login_required
def api_update_category(category_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    category = Category.query.get_or_404(category_id)
    data = request.json
    
    try:
        if 'name' in data:
            # Vérifier si le nom existe déjà (sauf pour cette catégorie)
            existing = Category.query.filter(
                Category.name == data['name'],
                Category.id != category_id
            ).first()
            if existing:
                return jsonify({'success': False, 'message': 'Ce nom de catégorie existe déjà'}), 400
            category.name = data['name']
        
        if 'description' in data:
            category.description = data['description']
        if 'icon' in data:
            category.icon = data['icon']
        if 'is_active' in data:
            category.is_active = bool(data['is_active'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '✅ Catégorie mise à jour avec succès!',
            'category': category.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/admin/api/categories/<int:category_id>', methods=['DELETE'])
@login_required
def api_delete_category(category_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    category = Category.query.get_or_404(category_id)
    
    try:
        # Vérifier si la catégorie est utilisée par des produits
        if category.products:
            return jsonify({
                'success': False, 
                'message': '❌ Impossible de supprimer: catégorie utilisée par des produits'
            }), 400
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '✅ Catégorie supprimée avec succès!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

# Routes existantes (inchangées)
@app.route('/admin/get-user-details/<int:user_id>')
@login_required
def get_user_details(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@app.route('/admin/activate-user', methods=['POST'])
@login_required
def admin_activate_user():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    token = request.json.get('token')
    user_id = request.json.get('user_id')
    
    if not token:
        return jsonify({'success': False, 'message': 'Token manquant'}), 400
    
    if user_id:
        user = User.query.get(user_id)
        if user and user.activation_token != token:
            return jsonify({
                'success': False,
                'message': '❌ Token incorrect pour cet utilisateur'
            }), 400
    else:
        user = User.query.filter_by(activation_token=token).first()
    
    if user:
        user.whatsapp_verified = True
        db.session.commit()
        
        send_activation_confirmation_whatsapp(user)
        
        return jsonify({
            'success': True,
            'message': f'✅ WhatsApp de {user.first_name} {user.last_name} vérifié!'
        })
    else:
        return jsonify({
            'success': False,
            'message': '❌ Token invalide'
        }), 404

@app.route('/admin/confirm-order/<order_id>', methods=['POST'])
@login_required
def confirm_order(order_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    order = Order.query.filter_by(whatsapp_order_id=order_id).first()
    
    if not order:
        return jsonify({
            'success': False,
            'message': '❌ Commande non trouvée'
        }), 404
    
    order.status = 'confirme'
    order.admin_confirmed_at = datetime.now(timezone.utc)
    db.session.commit()
    
    send_order_confirmation_whatsapp(order.customer, order)
    
    return jsonify({
        'success': True,
        'message': f'✅ Commande {order_id} confirmée!'
    })

@app.route('/admin/update-order-status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    order = Order.query.get_or_404(order_id)
    new_status = request.json.get('status')
    
    if not new_status:
        return jsonify({'success': False, 'message': 'Statut manquant'}), 400
    
    order.status = new_status
    if new_status == 'confirme' and not order.admin_confirmed_at:
        order.admin_confirmed_at = datetime.now(timezone.utc)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'✅ Statut de la commande mis à jour: {new_status}'
    })

@app.route('/admin/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'Vous ne pouvez pas modifier votre propre statut'}), 400
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'✅ Statut admin de {user.first_name} {user.last_name} modifié',
        'is_admin': user.is_admin
    })

# --- ROUTES PRINCIPALES ---
@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

@app.route('/')
def index():
    # Récupérer les paramètres de filtrage
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '')
    
    # Construction de la requête
    query = Product.query.filter_by(is_available=True).options(joinedload(Product.category_ref))
    
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))
    
    if category_filter:
        query = query.filter(Product.category_id == int(category_filter))
    
    products = query.all()
    categories = Category.query.filter_by(is_active=True).all()
    
    return render_template('index.html', 
                         products=products, 
                         categories=categories,
                         search_query=search_query,
                         category_filter=category_filter)

@app.route('/cart')
@login_required
def cart():
    return render_template('cart.html')

@app.route('/download-invoice/<int:order_id>')
@login_required
def download_invoice(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('index'))
    
    pdf_buffer = generate_invoice_pdf(order, order.customer)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f'facture-{order.whatsapp_order_id}.pdf',
        mimetype='application/pdf'
    )

# --- ROUTE CORRIGÉE POUR WHATSAPP ---
@app.route('/api/send-order-whatsapp', methods=['POST'])
@login_required
def send_order_whatsapp():
    if not current_user.whatsapp_verified:
        return jsonify({
            'success': False,
            'message': '❌ Veuillez vérifier votre WhatsApp avant de commander',
            'redirect': url_for('profile')
        }), 403
    
    data = request.get_json()  # CORRECTION: utiliser get_json() au lieu de .json
    print(f"📦 Données reçues: {data}")  # Debug
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'Données manquantes'
        }), 400
    
    cart_items = data.get('items', [])
    delivery_address = data.get('delivery_address', '')
    notes = data.get('notes', '')
    
    if not cart_items:
        return jsonify({
            'success': False,
            'message': 'Panier vide'
        }), 400
    
    try:
        # Créer la commande
        order = Order(user_id=current_user.id)
        order.generate_order_number()
        order.generate_whatsapp_order_id()
        order.delivery_address = delivery_address
        order.notes = notes
        
        total = 0
        items_added = 0
        
        for item in cart_items:
            product_id = item.get('product_id')
            if not product_id:
                continue
                
            product = Product.query.get(product_id)
            if not product or not product.is_available:
                print(f"❌ Produit non disponible: {product_id}")
                continue
            
            try:
                quantity = float(item.get('quantity', 0))
                if quantity <= 0:
                    continue
            except (ValueError, TypeError):
                print(f"❌ Quantité invalide: {item.get('quantity')}")
                continue

            subtotal = quantity * product.price
            total += subtotal
            
            order_item = OrderItem(
                product_id=product.id,
                product_name=product.name,
                quantity=quantity,
                unit_price=product.price,
                subtotal=subtotal
            )
            order.items.append(order_item)
            items_added += 1
        
        # Vérifier qu'au moins un article a été ajouté
        if items_added == 0:
            return jsonify({
                'success': False,
                'message': 'Aucun produit valide dans le panier'
            }), 400
        
        order.total_amount = total
        order.status = 'en_attente'
        
        db.session.add(order)
        db.session.commit()
        
        # Générer le lien WhatsApp APRÈS la création de la commande
        whatsapp_url = generate_order_whatsapp_link(
            cart_items, total, current_user, 
            order.whatsapp_order_id, delivery_address, notes
        )
        
        print(f"✅ Commande créée: {order.whatsapp_order_id}")
        print(f"🔗 Lien WhatsApp: {whatsapp_url}")
        
        return jsonify({
            'success': True,
            'message': f'✅ WhatsApp ouvert! ID de commande: {order.whatsapp_order_id}',
            'whatsapp_url': whatsapp_url,
            'order_id': order.whatsapp_order_id
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur création commande: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la création de commande: {str(e)}'
        }), 500

# Route de débogage
@app.route('/debug/cart', methods=['POST'])
@login_required
def debug_cart():
    data = request.get_json()
    print("🔍 DEBUG - Données reçues:")
    print(data)
    return jsonify({"received": True, "data": data})

# Initialisation de la base de données
def initialize_database():
    with app.app_context():
        try:
            print("🔧 Tentative de création des tables...")
            db.create_all()
            print("✅ Tables créées avec succès")
            
            # Créer l'admin
            admin = User.query.filter_by(email='sankarabienvenu226@gmail.com').first()
            if not admin:
                admin = User(
                    email='sankarabienvenu226@gmail.com',
                    phone='+22669628477',
                    first_name='Bienvenu',
                    last_name='Sankara',
                    email_verified=True,
                    whatsapp_verified=True,
                    is_active=True,
                    is_admin=True,
                    created_at=datetime.now(timezone.utc)
                )
                admin.set_password('Capi5688@1234')
                db.session.add(admin)
                print("✅ Compte admin créé: sankarabienvenu226@gmail.com")
            
            # Créer les catégories par défaut
            if Category.query.count() == 0:
                default_categories = [
                    {'name': 'Bœuf', 'description': 'Viandes de bœuf', 'icon': 'fas fa-drumstick-bite'},
                    {'name': 'Mouton', 'description': 'Viandes de mouton', 'icon': 'fas fa-paw'},
                    {'name': 'Volaille', 'description': 'Poulet et autres volailles', 'icon': 'fas fa-kiwi-bird'},
                    {'name': 'Porc', 'description': 'Viandes de porc', 'icon': 'fas fa-piggy-bank'},
                    {'name': 'Poisson', 'description': 'Poissons et fruits de mer', 'icon': 'fas fa-fish'},
                    {'name': 'Charcuterie', 'description': 'Saucisses et charcuteries', 'icon': 'fas fa-bacon'},
                    {'name': 'Autres', 'description': 'Autres produits', 'icon': 'fas fa-cube'}
                ]
                
                for cat_data in default_categories:
                    category = Category(**cat_data)
                    db.session.add(category)
                print("✅ Catégories par défaut créées")
            
            # Créer des produits de démonstration
            if Product.query.count() == 0:
                # Récupérer les catégories
                boeuf = Category.query.filter_by(name='Bœuf').first()
                mouton = Category.query.filter_by(name='Mouton').first()
                volaille = Category.query.filter_by(name='Volaille').first()
                
                products = [
                    {
                        'name': 'Bœuf - Entrecôte',
                        'description': 'Viande de qualité premium, tendre et savoureuse',
                        'price': 4500,
                        'unit': 'kg',
                        'category_id': boeuf.id,
                        'stock': 50,
                        'is_available': True
                    },
                    {
                        'name': 'Mouton - Gigot',
                        'description': 'Gigot de mouton frais, idéal pour les grillades',
                        'price': 3800,
                        'unit': 'kg',
                        'category_id': mouton.id,
                        'stock': 30,
                        'is_available': True
                    },
                    {
                        'name': 'Poulet entier',
                        'description': 'Poulet fermier de qualité supérieure',
                        'price': 2500,
                        'unit': 'pièce',
                        'category_id': volaille.id,
                        'stock': 100,
                        'is_available': True
                    }
                ]
                for p in products:
                    product = Product(**p)
                    db.session.add(product)
                print("✅ Produits de démonstration ajoutés")
            
            db.session.commit()
            print("🎉 Base de données initialisée avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur d'initialisation: {e}")
            db.session.rollback()

# FORCER L'INITIALISATION AU DÉMARRAGE
if __name__ == '__main__':
    with app.app_context():
        print("🔧 DÉMARRAGE DE L'APPLICATION...")
        initialize_database()
    
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    print(f"🌐 Démarrage sur le port {port} (debug: {debug_mode})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)