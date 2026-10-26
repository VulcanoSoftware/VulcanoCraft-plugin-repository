import unittest
from unittest.mock import patch
import mongomock

mongo_patcher = patch('pymongo.MongoClient', mongomock.MongoClient)
mongo_patcher.start()

import webserver
from webserver import app, db, hash_password

class TestVersionPinning(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.secret_key = 'test_secret'
        self.client = app.test_client()
        webserver.limiter.reset()

        # Reset collections
        db.users.delete_many({})
        db.plugins.delete_many({})

        # Insert test users
        db.users.insert_one({
            'username': 'owner_user',
            'password': hash_password('password123'),
            'role': 'user'
        })
        db.users.insert_one({
            'username': 'other_user',
            'password': hash_password('password123'),
            'role': 'user'
        })
        db.users.insert_one({
            'username': 'admin_user',
            'password': hash_password('admin123'),
            'role': 'admin'
        })

        # Insert test plugin
        db.plugins.insert_one({
            'url': 'https://modrinth.com/plugin/test-plugin',
            'title': 'Test Plugin',
            'owner': 'owner_user',
            'version': '1.0.0',
            'versions': '1.0.0 1.1.0 1.2.0'
        })

    def login(self, username, password='password123'):
        return self.client.post('/login', json={
            'username': username,
            'password': password
        })

    def test_pin_version_owner_success(self):
        self.login('owner_user', 'password123')
        res = self.client.post('/api/plugin/pin_version', json={
            'url': 'https://modrinth.com/plugin/test-plugin',
            'pinned_version': '1.0.0'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('pinned_version'), '1.0.0')

        plugin = db.plugins.find_one({'url': 'https://modrinth.com/plugin/test-plugin'})
        self.assertEqual(plugin.get('pinned_version'), '1.0.0')

    def test_pin_version_with_ingame_version_format(self):
        self.login('owner_user', 'password123')
        res = self.client.post('/api/plugin/pin_version', json={
            'url': 'https://modrinth.com/plugin/test-plugin',
            'pinned_version': '2.4.1 (1.21.6)'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('pinned_version'), '2.4.1 (1.21.6)')

        plugin = db.plugins.find_one({'url': 'https://modrinth.com/plugin/test-plugin'})
        self.assertEqual(plugin.get('pinned_version'), '2.4.1 (1.21.6)')

    def test_unpin_version_owner_success(self):
        db.plugins.update_one({'url': 'https://modrinth.com/plugin/test-plugin'}, {'$set': {'pinned_version': '1.0.0'}})
        self.login('owner_user', 'password123')

        res = self.client.post('/api/plugin/pin_version', json={
            'url': 'https://modrinth.com/plugin/test-plugin',
            'pinned_version': None
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIsNone(data.get('pinned_version'))

        plugin = db.plugins.find_one({'url': 'https://modrinth.com/plugin/test-plugin'})
        self.assertNotIn('pinned_version', plugin)

    def test_pin_version_forbidden_for_non_owner(self):
        self.login('other_user', 'password123')
        res = self.client.post('/api/plugin/pin_version', json={
            'url': 'https://modrinth.com/plugin/test-plugin',
            'pinned_version': '1.0.0'
        })
        self.assertEqual(res.status_code, 404)

    def test_pin_version_admin_override(self):
        self.login('admin_user', 'admin123')
        res = self.client.post('/api/plugin/pin_version', json={
            'url': 'https://modrinth.com/plugin/test-plugin',
            'pinned_version': '1.1.0'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))

        plugin = db.plugins.find_one({'url': 'https://modrinth.com/plugin/test-plugin'})
        self.assertEqual(plugin.get('pinned_version'), '1.1.0')

    def test_pin_version_unauthenticated(self):
        res = self.client.post('/api/plugin/pin_version', json={
            'url': 'https://modrinth.com/plugin/test-plugin',
            'pinned_version': '1.0.0'
        })
        self.assertEqual(res.status_code, 401)

if __name__ == '__main__':
    unittest.main()
