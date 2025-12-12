import hashlib
import os
from pymongo import MongoClient

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_admin():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db_name = os.getenv("MONGO_DB_NAME", "vulcanocraft")
    mongo_client = MongoClient(mongo_uri)
    db = mongo_client[mongo_db_name]
    users_collection = db.users
    existing_admin = users_collection.find_one({"username": "admin"})
    if existing_admin:
        print("Admin user already exists!")
        return
    default_password = os.getenv("ADMIN_DEFAULT_PASSWORD", "admin123")
    admin_user = {
        "username": "admin",
        "password": hash_password(default_password),
        "role": "admin"
    }
    users_collection.insert_one(admin_user)
    print("Admin user created!")
    print("Username: admin")
    print(f"Password: {default_password}")
    print("Role: admin")

if __name__ == '__main__':
    create_admin()
