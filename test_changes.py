import requests
import time

BASE_URL = "http://localhost:5000"
SESSION = requests.Session()

def login(username, password):
    url = f"{BASE_URL}/admin/login"
    payload = {"username": username, "password": password}
    response = SESSION.post(url, json=payload)
    if response.status_code == 200:
        print(f"Login successful for {username}")
        return True
    else:
        print(f"Login failed: {response.text}")
        return False

def test_categories_crud():
    print("\n--- Testing Categories CRUD ---")

    # 1. Get initial categories
    resp = SESSION.get(f"{BASE_URL}/admin/categories")
    if resp.status_code != 200:
        print(f"Failed to get categories: {resp.text}")
        return False
    initial_cats = resp.json()
    print(f"Initial categories: {initial_cats}")

    # 2. Add new category
    new_cat = "TestCategory"
    resp = SESSION.post(f"{BASE_URL}/admin/categories", json={"name": new_cat})
    if resp.status_code != 200:
        print(f"Failed to add category: {resp.text}")
        return False
    print(f"Added category '{new_cat}'")

    # Verify it exists
    resp = SESSION.get(f"{BASE_URL}/admin/categories")
    if new_cat not in resp.json():
        print("New category not found in list!")
        return False

    # 3. Rename category
    renamed_cat = "RenamedCategory"
    resp = SESSION.put(f"{BASE_URL}/admin/categories/{new_cat}", json={"new_name": renamed_cat})
    if resp.status_code != 200:
        print(f"Failed to rename category: {resp.text}")
        return False
    print(f"Renamed '{new_cat}' to '{renamed_cat}'")

    # Verify rename
    resp = SESSION.get(f"{BASE_URL}/admin/categories")
    cats = resp.json()
    if renamed_cat not in cats:
        print("Renamed category not found!")
        return False
    if new_cat in cats:
        print("Old category name still exists!")
        return False

    # 4. Delete category
    resp = SESSION.delete(f"{BASE_URL}/admin/categories/{renamed_cat}")
    if resp.status_code != 200:
        print(f"Failed to delete category: {resp.text}")
        return False
    print(f"Deleted category '{renamed_cat}'")

    # Verify deletion
    resp = SESSION.get(f"{BASE_URL}/admin/categories")
    if renamed_cat in resp.json():
        print("Category still exists after deletion!")
        return False

    print("Categories CRUD Passed!")
    return True

def test_add_plugin_with_category():
    print("\n--- Testing Add Plugin with Category ---")

    # We need to be logged in as a regular user to add plugins,
    # OR as admin (admin can also add user plugins? The code says add_user_plugin uses session['user'])
    # The session is already set to admin from previous step.

    plugin_data = {
        "url": "https://example.com/test-plugin",
        "title": "Test Plugin",
        "author": "Tester",
        "description": "A test plugin",
        "category": "Survival" # Assuming 'Survival' exists in default categories
    }

    resp = SESSION.post(f"{BASE_URL}/add_plugin", json={"plugin_data": plugin_data})
    if resp.status_code != 200:
        print(f"Failed to add plugin: {resp.text}")
        return False
    print("Added plugin with category 'Survival'")

    # Verify plugin has category
    # fetch /api/plugins/public or /admin/plugins
    resp = SESSION.get(f"{BASE_URL}/admin/plugins")
    plugins = resp.json()

    found = False
    for p in plugins:
        if p.get('url') == plugin_data['url']:
            found = True
            if p.get('category') == "Survival":
                print("Plugin correctly saved with category 'Survival'")
            else:
                print(f"Plugin saved but category is wrong: {p.get('category')}")
                return False
            break

    if not found:
        print("Plugin not found after adding!")
        return False

    # Cleanup: Delete the plugin
    resp = SESSION.post(f"{BASE_URL}/delete_plugin", json={"url": plugin_data['url']})
    if resp.status_code == 200:
        print("Cleanup: Test plugin deleted.")
    else:
        print(f"Cleanup failed: {resp.text}")

    print("Add Plugin Test Passed!")
    return True

if __name__ == "__main__":
    # Wait for server to start
    time.sleep(2)

    if login("admin", "admin123"):
        if test_categories_crud():
            test_add_plugin_with_category()
