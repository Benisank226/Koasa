import os
import sys

print("🔍 DIAGNOSTIC RAILWAY - VARIABLES D'ENVIRONNEMENT")
print("=" * 50)

# Vérifier les variables critiques
variables = [
    'DATABASE_URL',
    'SECRET_KEY', 
    'SMTP_SERVER',
    'SMTP_PORT',
    'SMTP_USERNAME',
    'SMTP_PASSWORD'
]

for var in variables:
    value = os.environ.get(var)
    if value:
        # Masquer les valeurs sensibles
        if 'PASSWORD' in var or 'SECRET' in var or 'KEY' in var:
            display_value = '***' + value[-4:] if len(value) > 4 else '***'
        elif 'DATABASE_URL' in var:
            display_value = value[:20] + '...' + value[-20:]
        else:
            display_value = value
            
        print(f"✅ {var}: {display_value}")
    else:
        print(f"❌ {var}: NON DÉFINIE")

print("=" * 50)

# Vérifier la connexion DB
try:
    from app import app, db
    with app.app_context():
        db.session.execute('SELECT 1')
        print("🎯 CONNEXION POSTGRESQL: ✅ RÉUSSIE")
        
        # Compter les tables
        from models import User, Product, Category
        users = User.query.count()
        products = Product.query.count()
        categories = Category.query.count()
        
        print(f"📊 STATISTIQUES BASE:")
        print(f"   👥 Utilisateurs: {users}")
        print(f"   🥩 Produits: {products}") 
        print(f"   📁 Catégories: {categories}")
        
except Exception as e:
    print(f"🎯 CONNEXION POSTGRESQL: ❌ ÉCHEC")
    print(f"   Erreur: {e}")

print("🔍 DIAGNOSTIC TERMINÉ")