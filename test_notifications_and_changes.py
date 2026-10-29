import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import mongomock

mongo_patcher = patch('pymongo.MongoClient', mongomock.MongoClient)
mongo_patcher.start()

import webserver
from webserver import app, hash_password, db
import cron

class TestNotificationsAndChanges(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        webserver.limiter.reset()

        # Clean collections
        db.settings.delete_many({})
        db.notifications.delete_many({})
        db.plugin_changes.delete_many({})
        db.users.delete_many({})
        db.plugins.delete_many({})

    def test_cron_status_endpoint(self):
        resp_empty = self.app.get('/api/cron_status')
        self.assertEqual(resp_empty.status_code, 200)
        self.assertIsNone(resp_empty.get_json().get('last_fetched'))

        # Set status via cron
        cron.record_cron_status()

        resp_set = self.app.get('/api/cron_status')
        self.assertEqual(resp_set.status_code, 200)
        last_fetched = resp_set.get_json().get('last_fetched')
        self.assertIsNotNone(last_fetched)

    def test_notifications_endpoints(self):
        # Insert test notifications
        db.notifications.insert_one({
            "plugin_title": "EssentialsX",
            "type": "version_update",
            "message": "Nieuwe versie 1.20.4",
            "timestamp": "2025-02-24T12:00:00"
        })

        resp = self.app.get('/api/notifications')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        notifs = data.get('notifications', [])
        self.assertEqual(len(notifs), 1)
        self.assertEqual(notifs[0]['plugin_title'], "EssentialsX")
        self.assertEqual(data.get('unread_count'), 1)

        # Test page route
        resp_page = self.app.get('/notifications')
        self.assertEqual(resp_page.status_code, 200)

        # Test clear notifications unauthenticated -> 401
        clear_unauth = self.app.post('/api/notifications/clear')
        self.assertEqual(clear_unauth.status_code, 401)

        # Authenticate user
        db.users.insert_one({
            'username': 'notif_user',
            'password': hash_password('pass123'),
            'role': 'user'
        })
        with self.app.session_transaction() as sess:
            sess['user'] = 'notif_user'

        clear_resp = self.app.post('/api/notifications/clear')
        self.assertEqual(clear_resp.status_code, 200)
        self.assertTrue(clear_resp.get_json().get('success'))

        resp_after = self.app.get('/api/notifications')
        self.assertEqual(len(resp_after.get_json().get('notifications', [])), 0)

    def test_changes_between_dates(self):
        # Insert test change records with different dates
        db.plugin_changes.insert_many([
            {
                "plugin_title": "Plugin A",
                "action": "version_update",
                "details": "1.0 -> 1.1",
                "date": "2025-01-10",
                "timestamp": "2025-01-10T10:00:00"
            },
            {
                "plugin_title": "Plugin B",
                "action": "version_update",
                "details": "2.0 -> 2.1",
                "date": "2025-02-15",
                "timestamp": "2025-02-15T12:00:00"
            },
            {
                "plugin_title": "Plugin C",
                "action": "version_update",
                "details": "3.0 -> 3.1",
                "date": "2025-02-20",
                "timestamp": "2025-02-20T15:00:00"
            }
        ])

        # Test query for range 2025-02-01 to 2025-02-18
        resp = self.app.get('/api/changes?start_date=2025-02-01&end_date=2025-02-18')
        self.assertEqual(resp.status_code, 200)
        changes = resp.get_json().get('changes', [])
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]['plugin_title'], "Plugin B")

        # Test query for all changes
        resp_all = self.app.get('/api/changes')
        self.assertEqual(resp_all.status_code, 200)
        self.assertEqual(len(resp_all.get_json().get('changes', [])), 3)

    def test_discord_webhook_settings_and_test(self):
        db.users.insert_one({
            'username': 'discord_user',
            'password': hash_password('pass123'),
            'role': 'user'
        })

        # Unauthenticated request -> 401
        self.assertEqual(self.app.get('/api/user/discord_webhook').status_code, 401)

        with self.app.session_transaction() as sess:
            sess['user'] = 'discord_user'

        # Get initial webhook settings
        get_resp = self.app.get('/api/user/discord_webhook')
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.get_json().get('webhook_url'), '')
        self.assertFalse(get_resp.get_json().get('enabled'))

        # Save webhook settings
        post_resp = self.app.post('/api/user/discord_webhook', json={
            'webhook_url': 'https://discord.com/api/webhooks/12345/abcde',
            'enabled': True
        })
        self.assertEqual(post_resp.status_code, 200)
        self.assertTrue(post_resp.get_json().get('success'))

        user_db = db.users.find_one({'username': 'discord_user'})
        self.assertEqual(user_db.get('discord_webhook_url'), 'https://discord.com/api/webhooks/12345/abcde')
        self.assertTrue(user_db.get('discord_notifications_enabled'))

        # Test webhook endpoint with mocked requests.post
        with patch('requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 204
            mock_post.return_value = mock_resp

            test_resp = self.app.post('/api/user/discord_webhook/test', json={})
            self.assertEqual(test_resp.status_code, 200)
            self.assertTrue(test_resp.get_json().get('success'))

            mock_post.assert_called_once()

    def test_retention_purge(self):
        # Configure retention to 7 days
        db.settings.insert_one({"_id": "app_settings", "retention_days": 7})

        now = datetime.now()
        old_date = now - timedelta(days=10)
        recent_date = now - timedelta(days=2)

        db.notifications.insert_many([
            {"message": "Old notif", "created_at": old_date},
            {"message": "New notif", "created_at": recent_date}
        ])
        db.plugin_changes.insert_many([
            {"details": "Old change", "created_at": old_date},
            {"details": "New change", "created_at": recent_date}
        ])

        cron.purge_old_records()

        self.assertEqual(db.notifications.count_documents({}), 1)
        self.assertEqual(db.plugin_changes.count_documents({}), 1)

        remaining_notif = db.notifications.find_one({})
        self.assertEqual(remaining_notif['message'], "New notif")

    def test_detect_and_record_changes(self):
        existing = {
            "url": "https://spigotmc.org/resources/999",
            "title": "My Plugin",
            "latest_version": "1.0.0"
        }
        updated = {
            "url": "https://spigotmc.org/resources/999",
            "title": "My Plugin",
            "latest_version": "1.1.0",
            "category": "Survival"
        }

        with patch('cron.requests.post') as mock_post:
            cron.detect_and_record_changes(existing, updated, owner="test_owner")

        notif = db.notifications.find_one({"url": "https://spigotmc.org/resources/999"})
        self.assertIsNotNone(notif)
        self.assertEqual(notif['old_version'], "1.0.0")
        self.assertEqual(notif['new_version'], "1.1.0")

        change = db.plugin_changes.find_one({"url": "https://spigotmc.org/resources/999"})
        self.assertIsNotNone(change)
        self.assertEqual(change['old_version'], "1.0.0")
        self.assertEqual(change['new_version'], "1.1.0")

if __name__ == '__main__':
    unittest.main()
