import hashlib
import sys
from database import get_users_collection

def hash_password(password):
    """Hash een wachtwoord met SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_admin(username, password):
    """
    Maakt een admin-gebruiker aan in de database of werkt deze bij.
    Gebruikt de opgegeven username en password.
    """
    users_collection = get_users_collection()
    
    # Hash het wachtwoord
    hashed_password = hash_password(password)
    
    # Maak het admin-gebruiker object aan
    admin_user = {
        'username': username,
        'password': hashed_password,
        'role': 'admin'
    }
    
    # Controleer of de gebruiker al bestaat en werk deze bij (upsert)
    result = users_collection.update_one(
        {'username': username},
        {'$set': admin_user},
        upsert=True
    )
    
    if result.upserted_id is not None:
        print(f"Admin-gebruiker '{username}' succesvol aangemaakt.")
    else:
        print(f"Admin-gebruiker '{username}' succesvol bijgewerkt.")

    print("-" * 30)
    print(f"Gebruikersnaam: {username}")
    print(f"Wachtwoord: {password}")
    print("Rol: admin")
    print("-" * 30)

if __name__ == '__main__':
    # Bepaal de gebruikersnaam en het wachtwoord
    # Gebruik de command-line argumenten als ze worden meegegeven
    # Anders, gebruik de standaardwaarden 'admin' en 'admin123'
    if len(sys.argv) == 3:
        admin_username = sys.argv[1]
        admin_password = sys.argv[2]
        print(f"Gebruiken van opgegeven credentials: '{admin_username}'")
    else:
        admin_username = 'admin'
        admin_password = 'admin123'
        print("Gebruiken van standaard credentials: 'admin' / 'admin123'")
        print("Tip: Je kunt custom credentials meegeven: python create_admin.py <username> <password>")

    # Roep de functie aan om de admin aan te maken
    create_admin(admin_username, admin_password)
