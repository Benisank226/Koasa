# migrate_database.py
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def migrate_database():
    with app.app_context():
        print("🔧 Migration de la base de données...")
        
        try:
            # Vérifier si la table orders existe
            result = db.session.execute(text("""
                SELECT column_name, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'orders' AND column_name = 'whatsapp_order_id'
            """))
            
            column_info = result.fetchone()
            
            if column_info:
                current_length = column_info[1]
                print(f"📊 Longueur actuelle de whatsapp_order_id: {current_length}")
                
                if current_length < 25:
                    print("🔄 Modification de la longueur de whatsapp_order_id...")
                    db.session.execute(text("""
                        ALTER TABLE orders 
                        ALTER COLUMN whatsapp_order_id TYPE VARCHAR(25)
                    """))
                    
                    print("🔄 Modification de la longueur de order_number...")
                    db.session.execute(text("""
                        ALTER TABLE orders 
                        ALTER COLUMN order_number TYPE VARCHAR(30)
                    """))
                    
                    db.session.commit()
                    print("✅ Migration réussie!")
                else:
                    print("✅ La base de données est déjà à jour")
            else:
                print("❌ Colonne whatsapp_order_id non trouvée")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la migration: {e}")
            print("💡 Essayez de supprimer et recréer les tables...")
            
            # Option de secours: recréer les tables
            try:
                print("🔄 Recréation des tables...")
                db.drop_all()
                db.create_all()
                print("✅ Tables recréées avec succès!")
            except Exception as e2:
                print(f"❌ Erreur lors de la recréation: {e2}")

if __name__ == '__main__':
    migrate_database()