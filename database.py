import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Laad omgevingsvariabelen uit .env-bestand
load_dotenv()

# Haal MongoDB verbindingsgegevens op uit omgevingsvariabelen
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "vulcanocraft")

# Maak de MongoDB client en database objecten aan
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

def get_plugins_collection():
    """Retourneert de 'plugins' collectie."""
    return db.plugins

def get_users_collection():
    """Retourneert de 'users' collectie."""
    return db.users

def get_server_categories_collection():
    """Retourneert de 'server_categories' collectie."""
    return db.server_categories

def get_settings_collection():
    """Retourneert de 'settings' collectie."""
    return db.settings

def get_loaders_collection():
    """Retourneert de 'loaders' collectie."""
    return db.loaders

def init_db():
    """Initialiseert de database met standaardwaarden als de collecties leeg zijn."""
    # Initialiseer settings als de collectie leeg is
    settings_collection = get_settings_collection()
    if settings_collection.count_documents({}) == 0:
        print("Initialiseren van de 'settings' collectie...")
        settings_collection.insert_one({'registration_enabled': True})
        print("'settings' collectie geïnitialiseerd.")

    # Voeg hier eventuele andere initialisatielogica toe,
    # bijvoorbeeld voor standaard categorieën of loaders.

if __name__ == '__main__':
    # Voer de initialisatiefunctie uit wanneer het script direct wordt uitgevoerd
    print("Database initialisatie script wordt uitgevoerd...")
    init_db()
    print("Database initialisatie voltooid.")
