import unittest
from unittest.mock import MagicMock, patch
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

    @patch('fetchers.versions.requests.get')
    def test_get_spigot_game_versions_without_pin_format(self, mock_get):
        class MockResponse:
            def __init__(self, json_data, status_code=200):
                self._json = json_data
                self.status_code = status_code
            def json(self):
                return self._json

        def side_effect(url, **kwargs):
            if '/resources/42464/versions' in url:
                return MockResponse([])
            elif '/resources/42464' in url:
                return MockResponse({'testedVersions': ['1.21', '1.20']})
            return MockResponse({}, status_code=404)

        mock_get.side_effect = side_effect

        from fetchers.versions import get_spigot_game_versions
        versions = get_spigot_game_versions('https://www.spigotmc.org/resources/paper-money.42464/')
        self.assertEqual(versions, ['1.20', '1.21'])

    @patch('fetchers.versions.requests.get')
    def test_get_spigot_game_versions_with_pin_format(self, mock_get):
        class MockResponse:
            def __init__(self, json_data, status_code=200):
                self._json = json_data
                self.status_code = status_code
            def json(self):
                return self._json

        def side_effect(url, **kwargs):
            if '/resources/42464/versions' in url:
                return MockResponse([
                    {'id': 594993, 'name': '1.21.4.a.1'},
                    {'id': 577104, 'name': 'v1.21.0.b.2'}
                ])
            elif '/resources/42464' in url:
                return MockResponse({'testedVersions': ['1.21']})
            return MockResponse({}, status_code=404)

        mock_get.side_effect = side_effect

        from fetchers.versions import get_spigot_game_versions, _fetch_platform_versions
        versions = get_spigot_game_versions('https://www.spigotmc.org/resources/paper-money.42464/', pin_format=True)
        self.assertIn('1.21.4.a.1 (1.21)', versions)
        self.assertIn('1.21.0.b.2 (1.21)', versions)

        fetched = _fetch_platform_versions('spigot', 'https://www.spigotmc.org/resources/paper-money.42464/', pin_format=True)
        self.assertEqual(fetched[0], '1.21.4.a.1 (1.21)')
        self.assertEqual(fetched[1], '1.21.0.b.2 (1.21)')

    @patch('fetchers.versions.requests.get')
    def test_get_bukkitdev_game_versions_sorting_and_clean_version(self, mock_get):
        class MockResponse:
            def __init__(self, json_data, status_code=200):
                self._json = json_data
                self.status_code = status_code
            def json(self):
                return self._json

        def side_effect(url, **kwargs):
            if 'projects?search=vault' in url:
                return MockResponse([{'id': 33437, 'slug': 'vault'}])
            elif 'files?projectIds=33437' in url:
                return MockResponse([
                    {'id': 10, 'name': 'Vault 1.0', 'gameVersion': 'CB 1337', 'dateReleased': '/Date(1000000000000)/'},
                    {'id': 20, 'name': 'Vault 1.7.2', 'gameVersion': 'CB 1.7.2-R0.3', 'dateReleased': '/Date(1400000000000)/'},
                ])
            return MockResponse([], status_code=404)

        mock_get.side_effect = side_effect

        from fetchers.versions import get_bukkitdev_game_versions
        # Pinned format should put newest release first and clean game versions
        pinned = get_bukkitdev_game_versions('vault', pin_format=True)
        self.assertEqual(len(pinned), 2)
        self.assertEqual(pinned[0], '1.7.2 (1.7.2)')
        self.assertEqual(pinned[1], '1.0')

    def test_parse_curseforge_versions_latest_files(self):
        from fetchers.versions import _parse_curseforge_versions
        mod_data = [{
            'latestFiles': [
                {
                    'id': 200,
                    'displayName': 'TestMod 2.0.0',
                    'gameVersions': ['1.20.1', '1.20.2', 'Forge']
                },
                {
                    'id': 100,
                    'displayName': 'TestMod 1.0.0',
                    'gameVersions': ['1.19.4', 'Fabric']
                }
            ]
        }]
        pinned = _parse_curseforge_versions(mod_data, pin_format=True)
        self.assertIn('2.0.0 (1.20.1)', pinned)
        self.assertIn('2.0.0 (1.20.2)', pinned)
        self.assertIn('1.0.0 (1.19.4)', pinned)

    def test_parse_curseforge_versions_with_filename_key(self):
        from fetchers.versions import _parse_curseforge_versions
        mod_data = [{
            'latestFilesIndexes': [
                {
                    'fileId': 500,
                    'filename': 'PlayerVaultsX-4.1.2.jar',
                    'gameVersion': '1.16'
                },
                {
                    'fileId': 400,
                    'filename': 'PlayerVaultsX-4.1.1.jar',
                    'gameVersion': '1.15'
                }
            ]
        }]
        pinned = _parse_curseforge_versions(mod_data, pin_format=True)
        self.assertIn('4.1.2 (1.16)', pinned)
        self.assertIn('4.1.1 (1.15)', pinned)

    def test_parse_curseforge_multi_game_versions_indexes(self):
        from fetchers.versions import _parse_curseforge_versions
        mod_data = [{
            'latestFilesIndexes': [
                {
                    'fileId': 500,
                    'filename': 'TAB-5.0.4.jar',
                    'gameVersion': '1.21'
                },
                {
                    'fileId': 500,
                    'filename': 'TAB-5.0.4.jar',
                    'gameVersion': '1.20'
                },
                {
                    'fileId': 500,
                    'filename': 'TAB-5.0.4.jar',
                    'gameVersion': '1.19'
                },
                {
                    'fileId': 400,
                    'filename': 'TAB-5.0.3.jar',
                    'gameVersion': '1.21'
                }
            ]
        }]
        pinned = _parse_curseforge_versions(mod_data, pin_format=True)
        self.assertIn('5.0.4 (1.21)', pinned)
        self.assertIn('5.0.4 (1.20)', pinned)
        self.assertIn('5.0.4 (1.19)', pinned)
        self.assertIn('5.0.3 (1.21)', pinned)

    def test_curseforge_game_version_not_plugin_version(self):
        from fetchers.versions import _parse_curseforge_versions
        mod_data = [{
            'latestFiles': [
                {
                    'id': 300,
                    'displayName': '1.20.1',
                    'fileName': '1.20.1.jar',
                    'gameVersions': ['1.20.1']
                },
                {
                    'id': 200,
                    'displayName': '1.19.4',
                    'fileName': 'Plugin-2.1.0.jar',
                    'gameVersions': ['1.19.4']
                }
            ]
        }]
        pinned = _parse_curseforge_versions(mod_data, pin_format=True)
        self.assertIn('1.20.1', pinned)
        self.assertNotIn('1.20.1 (1.20.1)', pinned)
        self.assertIn('2.1.0 (1.19.4)', pinned)

    @patch('fetchers.versions.requests.get')
    def test_bukkitdev_multi_game_versions_scraping(self, mock_get):
        from fetchers.versions import get_bukkitdev_game_versions
        html_content = '''
        <table>
            <tr class="project-file-list-item">
                <td><a data-action="file-link" href="/projects/tab/files/1000">TAB v5.0.4</a></td>
                <td class="project-file-game-version">
                    <span class="version-label">1.21</span>
                    <span class="additional-versions tip" title="<div>1.21</div><div>1.20</div><div>1.19</div><div>1.18</div><div>1.17</div><div>1.16</div>">+5</span>
                </td>
            </tr>
        </table>
        '''
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html_content
        mock_get.return_value = mock_resp

        pinned = get_bukkitdev_game_versions('tab', pin_format=True)
        self.assertEqual(len(pinned), 6)
        self.assertEqual(pinned[0], '5.0.4 (1.21)')
        self.assertEqual(pinned[1], '5.0.4 (1.20)')
        self.assertEqual(pinned[2], '5.0.4 (1.19)')
        self.assertEqual(pinned[3], '5.0.4 (1.18)')
        self.assertEqual(pinned[4], '5.0.4 (1.17)')
        self.assertEqual(pinned[5], '5.0.4 (1.16)')

    def test_sort_pin_versions_orders_plugin_versions_descending(self):
        from fetchers.versions import _sort_pin_versions
        raw_list = [
            '1.2 (1.18)',
            '1.3 (1.17)',
            '1.3 (1.18)',
            '0.2.1 (1.12)',
            '1.3 (1.16)',
            '2.0.0'
        ]
        sorted_list = _sort_pin_versions(raw_list)
        # 2.0.0 should be first, then 1.3 with game versions 1.18, 1.17, 1.16 in descending order, then 1.2, then 0.2.1
        self.assertEqual(sorted_list, [
            '2.0.0',
            '1.3 (1.18)',
            '1.3 (1.17)',
            '1.3 (1.16)',
            '1.2 (1.18)',
            '0.2.1 (1.12)'
        ])

if __name__ == '__main__':
    unittest.main()
