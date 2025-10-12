import os

print("🔍 DIAGNOSTIC DATABASE_URL SUR RAILWAY")
print("=" * 50)

database_url = os.environ.get('DATABASE_URL')
print(f"DATABASE_URL: {database_url}")

if database_url:
    print(f"Longueur: {len(database_url)}")
    print(f"Début: {database_url[:50]}...")
    print(f"Fin: ...{database_url[-20:]}")
    
    # Vérifier le format
    if database_url.startswith('postgres://'):
        print("✅ Format: postgres://")
        corrected_url = database_url.replace('postgres://', 'postgresql://', 1)
        print(f"URL corrigée: {corrected_url[:50]}...")
    elif database_url.startswith('postgresql://'):
        print("✅ Format: postgresql://")
    else:
        print("❌ Format inconnu")
else:
    print("❌ DATABASE_URL non définie")

print("=" * 50)