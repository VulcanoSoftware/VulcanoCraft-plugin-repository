import time
import urllib.request, json
import urllib.parse
import http.cookiejar

BASE_URL = 'http://localhost:5000'
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def request(method, url, data=None):
    if data:
        data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Content-Type', 'application/json')
    try:
        with opener.open(req) as response:
            return response.getcode(), json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return 0, str(e)

def login(username, password):
    code, resp = request('POST', f'{BASE_URL}/admin/login', {'username': username, 'password': password})
    if code == 200 and resp.get('success'):
        print(f'Login successful for {username}')
        return True
    print(f'Login failed: {resp}')
    return False

def test_categories_rename_regression():
    print('\n--- Testing Category Rename Regression ---')

    # 1. Create Category
    cat_name = 'RenameTestCat'
    request('POST', f'{BASE_URL}/admin/categories', {'name': cat_name})

    # 2. Create Plugin in that Category
    plugin_data = {
        'url': 'https://example.com/rename-test-plugin',
        'title': 'Rename Test Plugin',
        'author': 'Tester',
        'description': 'A test plugin for rename',
        'category': cat_name
    }
    code, resp = request('POST', f'{BASE_URL}/add_plugin', {'plugin_data': plugin_data})
    if code != 200: print(f'Failed to add plugin: {resp}'); return False

    # 3. Rename Category
    new_cat_name = 'RenamedTestCat'
    code, resp = request('PUT', f'{BASE_URL}/admin/categories/{cat_name}', {'new_name': new_cat_name})
    if code != 200: print(f'Failed to rename category: {resp}'); return False
    print(f"Category renamed from {cat_name} to {new_cat_name}")

    # 4. Check Plugin Category
    code, plugins = request('GET', f'{BASE_URL}/admin/plugins')
    found = False
    for p in plugins:
        if p.get('url') == plugin_data['url']:
            found = True
            if p.get('category') == new_cat_name:
                print(f'SUCCESS: Plugin category updated to {new_cat_name}')
            else:
                print(f'FAILURE: Plugin category is {p.get("category")}, expected {new_cat_name}')
                # cleanup
                request('POST', f'{BASE_URL}/delete_plugin', {'url': plugin_data['url']})
                request('DELETE', f'{BASE_URL}/admin/categories/{new_cat_name}')
                return False

    if not found: print('Plugin not found'); return False

    # Cleanup
    request('POST', f'{BASE_URL}/delete_plugin', {'url': plugin_data['url']})
    request('DELETE', f'{BASE_URL}/admin/categories/{new_cat_name}')
    print('Rename Regression Test Passed!')
    return True

if __name__ == "__main__":
    time.sleep(2)
    if login('admin', 'admin123'):
        test_categories_rename_regression()
