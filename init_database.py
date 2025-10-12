# init_database.py
import os
import sys

# Ajoute le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Product
from datetime import datetime, timezone

def init_database():
    with app.app_context():
        print("🔧 Initialisation de la base de données KOASA...")
        
        # Créer toutes les tables
        db.create_all()
        print("✅ Tables créées avec succès!")
        
        # Vérifier si l'admin existe déjà
        admin = User.query.filter_by(email='sankarabienvenu226@gmail.com').first()
        if not admin:
            # Créer l'admin
            admin = User(
                email='sankarabienvenu226@gmail.com',
                phone='+22669628477',
                first_name='Bienvenu',
                last_name='Sankara',
                email_verified=True,
                is_active=True,
                is_admin=True,
                whatsapp_verified=True,
                created_at=datetime.now(timezone.utc)
            )
            admin.set_password('Capi5688@1234')
            db.session.add(admin)
            db.session.commit()
            print("✅ Compte admin créé: admin@koasa.bf / admin123")
        else:
            print("ℹ️  Compte admin existe déjà")
        
        # Vérifier si des produits existent
        products_count = Product.query.count()
        if products_count == 0:
            # Ajouter des produits de démonstration
            products = [
                {
                    'name': 'Bœuf - Entrecôte',
                    'description': 'Viande de qualité premium, tendre et savoureuse',
                    'price': 4500,
                    'unit': 'kg',
                    'category': 'Bœuf',
                    'stock': 50
                },
                {
                    'name': 'Mouton - Gigot',
                    'description': 'Gigot de mouton frais, idéal pour les grillades',
                    'price': 3800,
                    'unit': 'kg',
                    'category': 'Mouton',
                    'stock': 30
                },
                {
                    'name': 'Poulet entier',
                    'description': 'Poulet fermier de qualité supérieure',
                    'price': 2500,
                    'unit': 'pièce',
                    'category': 'Volaille',
                    'stock': 100
                },
                {
                    'name': 'Côtelettes de porc',
                    'description': 'Côtelettes tendres, parfaites pour les grillades',
                    'price': 3200,
                    'unit': 'kg',
                    'category': 'Porc',
                    'stock': 40
                },
                {
                    'name': 'Saucisses de bœuf',
                    'description': 'Saucisses maison, savoureuses et épicées',
                    'price': 1800,
                    'unit': 'kg',
                    'category': 'Charcuterie',
                    'stock': 60
                }
            ]
            
            for p in products:
                product = Product(**p)
                db.session.add(product)
            
            db.session.commit()
            print(f"✅ {len(products)} produits ajoutés!")
        else:
            print(f"ℹ️  {products_count} produits existent déjà")
        
        print("🎉 Base de données initialisée avec succès!")
        print("\n📋 Comptes créés:")
        print("   Admin: admin@koasa.bf / admin123")
        print("\n📍 Accès:")
        print("   Application: http://localhost:5000")
        print("   Admin: http://localhost:5000/admin/users")

if __name__ == '__main__':
    init_database()