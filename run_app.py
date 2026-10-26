import unittest.mock as mock
import mongomock

# Patch MongoClient before importing webserver
mongo_patcher = mock.patch('pymongo.MongoClient', mongomock.MongoClient)
mongo_patcher.start()

import webserver

# Seed admin user and sample plugin data
webserver.db.users.delete_many({})
webserver.db.plugins.delete_many({})

webserver.db.users.insert_one({
    'username': 'admin',
    'password': webserver.hash_password('admin'),
    'role': 'admin'
})

webserver.db.plugins.insert_one({
    '_categoryContext': 'General',
    'added_at': '2026-10-26T08:37:56+00:00',
    'author': 'EssentialsX Team',
    'categories': ['General'],
    'category': 'General',
    'created_at': '2026-10-26T08:37:56+00:00',
    'description': 'Essential commands and utilities for Minecraft servers.',
    'icon': '',
    'last_modified': '2026-10-26T08:37:56+00:00',
    'loaders': ['Paper', 'Spigot'],
    'owner': 'admin',
    'pinned_version': '1.19',
    'title': 'EssentialsX',
    'updated_at': '2026-10-26T08:37:56+00:00',
    'url': 'https://modrinth.com/plugin/essentialsx',
    'versions': '1.18.2 1.19 1.19.4 1.20.1'
})

webserver.db.plugins.insert_one({
    '_categoryContext': 'General',
    'added_at': '2026-10-26T08:37:56+00:00',
    'author': 'sk89q',
    'categories': ['General'],
    'category': 'General',
    'created_at': '2026-10-26T08:37:56+00:00',
    'description': 'In-game Minecraft map editor.',
    'icon': '',
    'last_modified': '2026-10-26T08:37:56+00:00',
    'loaders': ['Paper', 'Spigot', 'Fabric'],
    'owner': 'admin',
    'title': 'WorldEdit',
    'updated_at': '2026-10-26T08:37:56+00:00',
    'url': 'https://modrinth.com/plugin/worldedit',
    'versions': '1.18.2 1.19 1.20.1'
})

if __name__ == '__main__':
    webserver.app.run(host='127.0.0.1', port=5000, debug=False)
