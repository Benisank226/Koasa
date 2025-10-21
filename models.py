from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    
    # Vérification email
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_code = db.Column(db.String(6), nullable=True)
    email_code_expires = db.Column(db.DateTime, nullable=True)
    
    # Activation WhatsApp (système original)
    activation_token = db.Column(db.String(100), unique=True, index=True)
    whatsapp_verified = db.Column(db.Boolean, default=False)
    
    # OTP pour vérification WhatsApp rapide
    otp_code = db.Column(db.String(6), nullable=True)
    otp_created_at = db.Column(db.DateTime, nullable=True)
    
    # Récupération mot de passe
    reset_token = db.Column(db.String(100), nullable=True, index=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    
    # Admin
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relations
    orders = db.relationship('Order', backref='customer', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_email_verification_code(self):
        self.email_verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        self.email_code_expires = datetime.now(timezone.utc) + timedelta(minutes=5)
        return self.email_verification_code
    
    def verify_email_code(self, code):
        if not self.email_verification_code or not self.email_code_expires:
            return False
        
        if datetime.now(timezone.utc) > self.email_code_expires.replace(tzinfo=timezone.utc):
            return False
        
        if self.email_verification_code == code:
            self.email_verified = True
            self.email_verification_code = None
            self.email_code_expires = None
            return True
        
        return False
    
    def generate_activation_token(self):
        self.activation_token = secrets.token_urlsafe(32)
        return self.activation_token
    
    def generate_otp(self):
        self.otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        self.otp_created_at = datetime.now(timezone.utc)
        return self.otp_code
    
    def verify_otp(self, code):
        if not self.otp_code or not self.otp_created_at:
            return False
        
        if datetime.now(timezone.utc) - self.otp_created_at.replace(tzinfo=timezone.utc) > timedelta(minutes=10):
            return False
        
        if self.otp_code == code:
            self.whatsapp_verified = True
            self.otp_code = None
            self.otp_created_at = None
            return True
        
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'phone': self.phone,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email_verified': self.email_verified,
            'whatsapp_verified': self.whatsapp_verified,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'activation_token': self.activation_token,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default='fas fa-cube')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relations
    products = db.relationship('Product', backref='category_ref', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'is_active': self.is_active,
            'product_count': len(self.products),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), default='kg')
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    image_url = db.Column(db.String(255))
    stock = db.Column(db.Integer, default=0)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'unit': self.unit,
            'category': self.category_ref.name if self.category_ref else 'Non catégorisé',
            'category_id': self.category_id,
            'category_ref': {
                'id': self.category_ref.id,
                'name': self.category_ref.name,
                'icon': self.category_ref.icon
            } if self.category_ref else None,
            'image_url': self.image_url,
            'stock': self.stock,
            'is_available': self.is_available,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_number = db.Column(db.String(30), unique=True, nullable=False, index=True)  # CORRIGÉ: 20 → 30
    whatsapp_order_id = db.Column(db.String(25), unique=True, nullable=False, index=True)  # CORRIGÉ: 20 → 25
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='en_attente')
    delivery_address = db.Column(db.Text)
    notes = db.Column(db.Text)
    admin_confirmed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def generate_order_number(self):
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        random_suffix = secrets.token_hex(3).upper()
        self.order_number = f"KO-{timestamp}-{random_suffix}"
        return self.order_number
    
    def generate_whatsapp_order_id(self):
        date_part = datetime.now(timezone.utc).strftime('%y%m%d')  # CORRIGÉ: %Y → %y (année sur 2 chiffres)
        random_part = secrets.token_hex(3).upper()
        self.whatsapp_order_id = f"CMD-{date_part}-{random_part}"  # Maintenant 18 caractères max
        return self.whatsapp_order_id
    
    def confirm_by_admin(self):
        self.status = 'confirme'
        self.admin_confirmed_at = datetime.now(timezone.utc)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'whatsapp_order_id': self.whatsapp_order_id,
            'total_amount': self.total_amount,
            'status': self.status,
            'delivery_address': self.delivery_address,
            'notes': self.notes,
            'admin_confirmed_at': self.admin_confirmed_at.isoformat() if self.admin_confirmed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'customer': {
                'first_name': self.customer.first_name,
                'last_name': self.customer.last_name,
                'email': self.customer.email,
                'phone': self.customer.phone
            },
            'items': [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product', backref='order_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': self.subtotal
        }