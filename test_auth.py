import unittest
import hashlib
from argon2 import PasswordHasher
import mongomock
from unittest.mock import patch

mongo_patcher = patch('pymongo.MongoClient', mongomock.MongoClient)
mongo_patcher.start()

import webserver
from webserver import app, hash_password, verify_password, db

class TestAuthArgon2(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

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

if __name__ == '__main__':
    unittest.main()
