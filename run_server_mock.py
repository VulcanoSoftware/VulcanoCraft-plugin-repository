from unittest.mock import patch
import mongomock

mongo_patcher = patch('pymongo.MongoClient', mongomock.MongoClient)
mongo_patcher.start()

import webserver
from webserver import db, app, hash_password

db.server_categories.insert_many([
    {'name': 'Survival', 'software': 'Paper', 'version': '1.20'},
    {'name': 'Lobby', 'software': 'Spigot', 'version': '1.20'}
])

db.users.insert_one({
    'username': 'admin',
    'password': hash_password('admin123'),
    'role': 'admin'
})

db.plugins.insert_one({
    'title': 'EssentialsX',
    'url': 'https://spigotmc.org/resources/1234',
    'author': 'TeamCity',
    'owner': 'admin',
    'category': 'Survival',
    'categories': ['Survival'],
    'versions': '1.20',
    'loaders': ['Paper']
})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
