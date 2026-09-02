import unittest
import hashlib
from argon2 import PasswordHasher
import mongomock
import sys
from unittest.mock import patch, MagicMock, call

mongo_patcher = patch('pymongo.MongoClient', mongomock.MongoClient)
mongo_patcher.start()

import webserver
from webserver import app, hash_password, verify_password, db

class TestAuthArgon2(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        webserver.limiter.reset()

    def test_argon2_hash_and_verify(self):
        password = "MySecurePassword123!"
        hashed = hash_password(password)

        self.assertTrue(hashed.startswith("$argon2"))

        is_valid, needs_rehash = verify_password(hashed, password)
        self.assertTrue(is_valid)
        self.assertFalse(needs_rehash)

        is_valid_wrong, _ = verify_password(hashed, "WrongPassword")
        self.assertFalse(is_valid_wrong)

    def test_legacy_sha256_verify_and_rehash(self):
        password = "LegacyPassword456!"
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()

        is_valid, needs_rehash = verify_password(legacy_hash, password)
        self.assertTrue(is_valid)
        self.assertTrue(needs_rehash)

        is_valid_wrong, _ = verify_password(legacy_hash, "WrongPassword")
        self.assertFalse(is_valid_wrong)

    def test_invalid_and_empty_passwords(self):
        self.assertEqual(verify_password(None, "pass"), (False, False))
        self.assertEqual(verify_password("", "pass"), (False, False))
        self.assertEqual(verify_password("some_hash", ""), (False, False))

    def test_register_and_login_argon2(self):
        db.users.delete_many({"username": "testuser_argon2"})

        reg_resp = self.app.post('/register', json={
            'username': 'testuser_argon2',
            'password': 'Password123!'
        })
        self.assertEqual(reg_resp.status_code, 200)

        user = db.users.find_one({"username": "testuser_argon2"})
        self.assertIsNotNone(user)
        self.assertTrue(user['password'].startswith("$argon2"))

        login_resp = self.app.post('/login', json={
            'username': 'testuser_argon2',
            'password': 'Password123!'
        })
        self.assertEqual(login_resp.status_code, 200)

        db.users.delete_many({"username": "testuser_argon2"})

    def test_legacy_user_login_migration(self):
        db.users.delete_many({"username": "legacy_user"})

        password = "LegacyUserSecret"
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()

        db.users.insert_one({
            'username': 'legacy_user',
            'password': legacy_hash,
            'role': 'user'
        })

        # Pre-login check: password is legacy SHA-256
        user_before = db.users.find_one({"username": "legacy_user"})
        self.assertEqual(user_before['password'], legacy_hash)

        # Login triggers auto-upgrade to Argon2
        login_resp = self.app.post('/login', json={
            'username': 'legacy_user',
            'password': password
        })
        self.assertEqual(login_resp.status_code, 200)

        # Post-login check: password is now Argon2 hash
        user_after = db.users.find_one({"username": "legacy_user"})
        self.assertTrue(user_after['password'].startswith("$argon2"))

        db.users.delete_many({"username": "legacy_user"})

    def test_admin_legacy_login_migration(self):
        db.users.delete_many({"username": "admin_legacy"})

        password = "AdminLegacySecret"
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()

        db.users.insert_one({
            'username': 'admin_legacy',
            'password': legacy_hash,
            'role': 'admin'
        })

        login_resp = self.app.post('/admin/login', json={
            'username': 'admin_legacy',
            'password': password
        })
        self.assertEqual(login_resp.status_code, 200)

        user_after = db.users.find_one({"username": "admin_legacy"})
        self.assertTrue(user_after['password'].startswith("$argon2"))

        db.users.delete_many({"username": "admin_legacy"})

    def test_change_password(self):
        db.users.delete_many({"username": "change_pass_user"})

        password = "OldPassword123!"
        hashed = hash_password(password)

        db.users.insert_one({
            'username': 'change_pass_user',
            'password': hashed,
            'role': 'user'
        })

        with self.app.session_transaction() as sess:
            sess['user'] = 'change_pass_user'

        resp = self.app.post('/api/change-password', json={
            'old_password': 'OldPassword123!',
            'new_password': 'NewPassword456!'
        })
        self.assertEqual(resp.status_code, 200)

        user_after = db.users.find_one({"username": "change_pass_user"})
        self.assertTrue(user_after['password'].startswith("$argon2"))

        is_valid, _ = verify_password(user_after['password'], 'NewPassword456!')
        self.assertTrue(is_valid)

        db.users.delete_many({"username": "change_pass_user"})

    def test_rate_limiting(self):
        # Perform requests to trigger rate limit (10 per minute)
        for i in range(10):
            self.app.post('/login', json={'username': 'nonexistent', 'password': 'wrong'})

        # 11th request should be rate limited
        resp = self.app.post('/login', json={'username': 'nonexistent', 'password': 'wrong'})
        self.assertEqual(resp.status_code, 429)
        data = resp.get_json()
        self.assertIn('Te veel verzoeken', data.get('error', ''))

    def test_nosql_injection_prevention(self):
        # Attempt NoSQL operator injection in username (sanitized to empty string -> 400 Bad Request)
        resp1 = self.app.post('/login', json={
            'username': {'$gt': ''},
            'password': 'somepassword'
        })
        self.assertIn(resp1.status_code, [400, 401])

        # Attempt NoSQL operator injection in password
        resp2 = self.app.post('/login', json={
            'username': 'admin',
            'password': {'$ne': None}
        })
        self.assertIn(resp2.status_code, [400, 401])

    @patch('subprocess.run')
    @patch('os._exit')
    def test_admin_apply_update_executes_pip_install(self, mock_exit, mock_subprocess_run):
        db.users.delete_many({"username": "admin_test"})
        db.users.insert_one({
            'username': 'admin_test',
            'password': hash_password('adminpass'),
            'role': 'admin'
        })

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Already up to date."
        mock_process.stderr = ""
        mock_subprocess_run.return_value = mock_process

        with self.app.session_transaction() as sess:
            sess['user'] = 'admin_test'

        resp = self.app.post('/admin/update/apply')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('success'))

        expected_calls = [
            call(['git', 'pull', 'origin', 'main'], capture_output=True, text=True, timeout=60),
            call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], capture_output=True, text=True, timeout=120)
        ]
        mock_subprocess_run.assert_has_calls(expected_calls, any_order=False)

        db.users.delete_many({"username": "admin_test"})

    def test_clear_plugins_user(self):
        db.users.delete_many({"username": "user_clear"})
        db.plugins.delete_many({"owner": "user_clear"})

        db.users.insert_one({
            'username': 'user_clear',
            'password': hash_password('clearpass'),
            'role': 'user'
        })
        db.plugins.insert_one({
            'title': 'Plugin 1',
            'url': 'https://spigotmc.org/resources/1',
            'owner': 'user_clear'
        })

        with self.app.session_transaction() as sess:
            sess['user'] = 'user_clear'

        resp = self.app.post('/api/plugins/clear')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('deleted_count'), 1)

        user_plugins = list(db.plugins.find({"owner": "user_clear"}))
        self.assertEqual(len(user_plugins), 0)

        db.users.delete_many({"username": "user_clear"})

    @patch('subprocess.run')
    @patch('os._exit')
    def test_admin_rollback_update(self, mock_exit, mock_subprocess_run):
        db.users.delete_many({"username": "admin_rollback"})
        db.users.insert_one({
            'username': 'admin_rollback',
            'password': hash_password('adminpass'),
            'role': 'admin'
        })

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "e24c88d5e6489593183622146742bca77ee26aef\n"
        mock_process.stderr = ""
        mock_subprocess_run.return_value = mock_process

        with self.app.session_transaction() as sess:
            sess['user'] = 'admin_rollback'

        resp = self.app.post('/admin/update/rollback')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('success'))

        db.users.delete_many({"username": "admin_rollback"})

if __name__ == '__main__':
    unittest.main()
