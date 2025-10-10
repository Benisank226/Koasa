import unittest
import os
import tempfile
from app import app, db
from models import User, Product, Order
from datetime import datetime, timezone

class TestApp(unittest.TestCase):
    
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_home_page(self):
        """Test de la page d'accueil"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'KOASA', response.data)
    
    def test_user_registration(self):
        """Test de l'inscription utilisateur"""
        response = self.client.post('/register', data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'phone': '+22670123456',
            'password': 'testpassword123',
            'confirm_password': 'testpassword123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que l'utilisateur a été créé
        with self.app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.first_name, 'Test')
            self.assertFalse(user.is_active)  # Doit être inactif avant activation
    
    def test_product_creation(self):
        """Test de création de produit"""
        with self.app.app_context():
            product = Product(
                name='Test Product',
                description='Test Description',
                price=1000,
                unit='kg',
                category='Test',
                stock=10
            )
            db.session.add(product)
            db.session.commit()
            
            saved_product = Product.query.filter_by(name='Test Product').first()
            self.assertIsNotNone(saved_product)
            self.assertEqual(saved_product.price, 1000)
    
    def test_order_creation(self):
        """Test de création de commande"""
        with self.app.app_context():
            # Créer un utilisateur
            user = User(
                email='test@example.com',
                phone='+22670123456',
                first_name='Test',
                last_name='User',
                is_active=True,
                whatsapp_verified=True,
                created_at=datetime.now(timezone.utc)
            )
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            # Créer un produit
            product = Product(
                name='Test Product',
                price=1000,
                unit='kg',
                stock=10
            )
            db.session.add(product)
            db.session.commit()
            
            # Créer une commande
            order = Order(user_id=user.id)
            order.generate_order_number()
            order.total_amount = 2000
            order.status = 'confirme'
            db.session.add(order)
            db.session.commit()
            
            saved_order = Order.query.filter_by(user_id=user.id).first()
            self.assertIsNotNone(saved_order)
            self.assertEqual(saved_order.total_amount, 2000)
    
    def test_admin_access(self):
        """Test d'accès admin"""
        with self.app.app_context():
            # Créer un utilisateur admin
            admin = User(
                email='admin@test.com',
                phone='+22670000000',
                first_name='Admin',
                last_name='Test',
                is_active=True,
                is_admin=True,
                created_at=datetime.now(timezone.utc)
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            
            # Tenter d'accéder à la page admin sans être connecté
            response = self.client.get('/admin/users', follow_redirects=True)
            self.assertIn(b'Connexion', response.data)  # Doit rediriger vers login
    
    def test_password_hashing(self):
        """Test du hachage des mots de passe"""
        with self.app.app_context():
            user = User(
                email='test@example.com',
                phone='+22670123456',
                first_name='Test',
                last_name='User',
                created_at=datetime.now(timezone.utc)
            )
            user.set_password('mysecurepassword')
            
            # Vérifier que le mot de passe est haché
            self.assertNotEqual(user.password_hash, 'mysecurepassword')
            self.assertTrue(user.check_password('mysecurepassword'))
            self.assertFalse(user.check_password('wrongpassword'))
    
    def test_otp_generation(self):
        """Test de génération OTP"""
        with self.app.app_context():
            user = User(
                email='test@example.com',
                phone='+22670123456',
                first_name='Test',
                last_name='User',
                created_at=datetime.now(timezone.utc)
            )
            
            otp = user.generate_otp()
            self.assertEqual(len(otp), 6)
            self.assertTrue(otp.isdigit())
            
            # Vérifier que l'OTP est valide
            self.assertTrue(user.verify_otp(otp))
            self.assertTrue(user.whatsapp_verified)
            
            # Vérifier qu'un OTP incorrect échoue
            user2 = User(
                email='test2@example.com',
                phone='+22670123457',
                first_name='Test2',
                last_name='User2',
                created_at=datetime.now(timezone.utc)
            )
            user2.generate_otp()
            self.assertFalse(user2.verify_otp('000000'))

if __name__ == '__main__':
    unittest.main()