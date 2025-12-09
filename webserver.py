from flask import Flask, jsonify, request, send_file, session
import os
import json as json_module
import subprocess
import sys
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

def load_plugins():
    """Laad de plugins data uit het JSON bestand"""
    try:
        if os.path.exists('plugins.json'):
            with open('plugins.json', 'r', encoding='utf-8') as f:
                return json_module.load(f)
        return []
    except Exception as e:
        print(f"Fout bij het laden van plugins: {e}")
        return []

def save_plugins(plugins):
    """Sla plugins op in het JSON bestand"""
    try:
        with open('plugins.json', 'w', encoding='utf-8') as f:
            json_module.dump(plugins, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Fout bij het opslaan van plugins: {e}")
        return False

def get_user_plugins(username):
    """Haal plugins van specifieke gebruiker op"""
    plugins = load_plugins()
    return [p for p in plugins if p.get('owner') == username]

def add_user_plugin(username, plugin_data):
    """Voeg plugin toe voor specifieke gebruiker"""
    plugins = load_plugins()
    plugin_data['owner'] = username
    plugins = [p for p in plugins if not (p.get('url') == plugin_data['url'] and p.get('owner') == username)]
    plugins.append(plugin_data)
    return save_plugins(plugins)

def delete_user_plugin(username, url):
    """Verwijder plugin van specifieke gebruiker"""
    plugins = load_plugins()
    new_plugins = [p for p in plugins if not (p.get('url') == url and p.get('owner') == username)]
    return save_plugins(new_plugins) if len(new_plugins) != len(plugins) else False

def delete_any_plugin(url):
    """Verwijder plugin (admin functie)"""
    plugins = load_plugins()
    new_plugins = [p for p in plugins if p.get('url') != url]
    return save_plugins(new_plugins) if len(new_plugins) != len(plugins) else False

def load_users():
    """Laad gebruikers uit users.json"""
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf-8') as f:
                return json_module.load(f)
        return []
    except Exception:
        return []

def save_users(users):
    """Sla gebruikers op in users.json"""
    try:
        with open('users.json', 'w', encoding='utf-8') as f:
            json_module.dump(users, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False

def hash_password(password):
    """Hash wachtwoord"""
    return hashlib.sha256(password.encode()).hexdigest()

def require_login(f):
    """Decorator voor login vereiste"""
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Login vereist'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def require_admin(f):
    """Decorator voor admin vereiste"""
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin rechten vereist'}), 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def require_co_admin(f):
    """Decorator voor co-admin of admin vereiste"""
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user.get('role') not in ['admin', 'co-admin']:
            return jsonify({'error': 'Co-Admin rechten vereist'}), 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def get_current_user():
    """Haal huidige gebruiker op"""
    if 'user' not in session:
        return None
    users = load_users()
    return next((u for u in users if u['username'] == session['user']), None)

def load_settings():
    """Laad instellingen"""
    try:
        if os.path.exists('settings.json'):
            with open('settings.json', 'r', encoding='utf-8') as f:
                return json_module.load(f)
        return {'registration_enabled': True}
    except Exception:
        return {'registration_enabled': True}

def save_settings(settings):
    """Sla instellingen op"""
    try:
        with open('settings.json', 'w', encoding='utf-8') as f:
            json_module.dump(settings, f, indent=4)
        return True
    except Exception:
        return False

def load_server_categories():
    """Laad server categorieën uit server_categories.json"""
    try:
        if os.path.exists('server_categories.json'):
            with open('server_categories.json', 'r', encoding='utf-8') as f:
                return json_module.load(f)
        return []
    except Exception:
        return []

def save_server_categories(categories):
    """Sla server categorieën op in server_categories.json"""
    try:
        with open('server_categories.json', 'w', encoding='utf-8') as f:
            json_module.dump(categories, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False

@app.route('/')
def index():
    """Serveer de index.html pagina"""
    return send_file('index.html')

@app.route('/login-page')
def login_page():
    """Serveer de login.html pagina"""
    return send_file('components/user/login.html')

@app.route('/change_password', methods=['GET', 'POST'])
def change_password_page():
    return send_file('components/user/change_password.html')


@app.route('/style.css')
def serve_css():
    """Serveer de CSS file"""
    return send_file('style.css', mimetype='text/css')

@app.route('/script.js')
def serve_js():
    """Serveer de JS file"""
    return send_file('script.js', mimetype='application/javascript')

@app.route('/js/<path:filename>')
def serve_js_from_folder(filename):
    """Serveer JS bestanden uit de js map"""
    try:
        return send_file(f'js/{filename}', mimetype='application/javascript')
    except FileNotFoundError:
        return "JavaScript file not found", 404
    
@app.route('/css/<path:filename>')
def serve_css_from_folder(filename):
    """Serveer CSS bestanden uit de css map"""
    try:
        return send_file(f'css/{filename}', mimetype='text/css')
    except FileNotFoundError:
        return "CSS file not found", 404

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serveer afbeeldingen uit de images map"""
    try:
        return send_file(f'images/{filename}')
    except FileNotFoundError:
        return "Image not found", 404

@app.route('/api/plugins')
@require_login
def api_plugins():
    """API endpoint voor plugins data van ingelogde gebruiker"""
    username = session['user']
    plugins = get_user_plugins(username)
    return jsonify(plugins)

@app.route('/api/plugins/public')
def api_plugins_public():
    """API endpoint voor alle plugins data (publiek toegankelijk)"""
    plugins = load_plugins()
    return jsonify(plugins)


@app.route('/api/server_categories')
def api_server_categories():
    """API endpoint returning a list of server categories."""
    categories = load_server_categories()
    return jsonify(categories)

@app.route('/api/server_info')
def api_server_info():
    """API endpoint for server software and version info for categories."""
    categories = load_server_categories()
    server_info = {}
    for category in categories:
        if 'name' in category:
            server_info[category['name']] = {
                'software': category.get('software', ''),
                'version': category.get('version', '')
            }
    return jsonify(server_info)

@app.route('/api/loaders')
def api_loaders():
    """API endpoint for loaders data"""
    try:
        if os.path.exists('loaders.json'):
            with open('loaders.json', 'r', encoding='utf-8') as f:
                loaders = json_module.load(f)
                return jsonify(loaders)
        return jsonify([])
    except Exception as e:
        print(f"Fout bij het laden van loaders: {e}")
        return jsonify({'error': 'Fout bij het laden van loaders'}), 500

@app.route('/register', methods=['POST'])
def register():
    """Registreer nieuwe gebruiker"""
    try:
        settings = load_settings()
        if not settings.get('registration_enabled', True):
            return jsonify({'error': 'Registratie is uitgeschakeld'}), 403
            
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Gebruikersnaam en wachtwoord zijn vereist'}), 400
        
        users = load_users()
        
        # Check of gebruiker al bestaat
        if any(u['username'] == username for u in users):
            return jsonify({'error': 'Gebruikersnaam bestaat al'}), 400
        
        # Voeg nieuwe gebruiker toe
        users.append({
            'username': username,
            'password': hash_password(password),
            'role': 'user'
        })
        
        if save_users(users):
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Fout bij opslaan'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    """Login gebruiker"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Gebruikersnaam en wachtwoord vereist'}), 400
        
        users = load_users()
        hashed_password = hash_password(password)
        
        # Check username
        user = next((u for u in users if u['username'] == username and u['password'] == hashed_password), None)
        
        if user:
            session['user'] = user['username']
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Ongeldige inloggegevens'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout', methods=['POST'])
def logout():
    """Logout gebruiker"""
    session.pop('user', None)
    return jsonify({'success': True})

@app.route('/api/change-password', methods=['POST'])
@require_login
def change_password():
    """Wijzig het wachtwoord van de ingelogde gebruiker"""
    try:
        data = request.get_json()
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')

        if not old_password or not new_password:
            return jsonify({'error': 'Oud en nieuw wachtwoord zijn vereist'}), 400

        user = get_current_user()
        if not user:
            return jsonify({'error': 'Gebruiker niet ingelogd'}), 401

        print(f"DEBUG: old_password: {old_password}")
        print(f"DEBUG: new_password: {new_password}")
        print(f"DEBUG: user: {user}")

        # Controleer of het oude wachtwoord correct is
        hashed_old_password = hash_password(old_password)
        print(f"DEBUG: hashed_old_password: {hashed_old_password}")
        print(f"DEBUG: user['password']: {user['password']}")
        if hashed_old_password != user['password']:
            print("DEBUG: Old password mismatch")
            return jsonify({'error': 'Oud wachtwoord is onjuist'}), 401

        # Update het wachtwoord
        users = load_users()
        for u in users:
            if u['username'] == user['username']:
                u['password'] = hash_password(new_password)
                print(f"DEBUG: Updating password for user {u['username']} to {u['password']}")
                break
        
        save_success = save_users(users)
        print(f"DEBUG: save_users success: {save_success}")
        if save_success:
            return jsonify({'success': True, 'message': 'Wachtwoord succesvol gewijzigd'})
        else:
            return jsonify({'error': 'Fout bij opslaan van nieuw wachtwoord'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth-status')
def auth_status():
    """Check login status"""
    user = get_current_user()
    return jsonify({
        'logged_in': 'user' in session, 
        'username': session.get('user'),
        'role': user.get('role', 'user') if user else 'user'
    })

@app.route('/registration-status')
def registration_status():
    """Check if registration is enabled"""
    settings = load_settings()
    return jsonify({'enabled': settings.get('registration_enabled', True)})



@app.route('/admin')
def admin_panel():
    """Admin panel pagina"""
    return send_file('components/admin/admin.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    users = load_users()
    user = next((u for u in users if u['username'] == username and u['password'] == hash_password(password)), None)
    
    if user and user.get('role') in ['admin', 'co-admin']:
        session['user'] = username
        return jsonify({'success': True, 'role': user.get('role')})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Admin logout"""
    session.pop('user', None)
    return jsonify({'success': True})

@app.route('/admin/check-session')
def admin_check_session():
    """Check admin session status"""
    user = get_current_user()
    if user and user.get('role') in ['admin', 'co-admin']:
        return jsonify({'logged_in': True, 'role': user.get('role'), 'username': user.get('username')})
    return jsonify({'logged_in': False})

@app.route('/admin/users', methods=['GET'])
@require_co_admin
def admin_get_users():
    """Haal alle gebruikers op met plugin counts"""
    users = load_users()
    plugins = load_plugins()
    
    user_data = []
    for u in users:
        plugin_count = len([p for p in plugins if p.get('owner') == u['username']])
        user_data.append({
            'username': u['username'], 
            'role': u.get('role', 'user'),
            'plugin_count': plugin_count
        })
    
    return jsonify(user_data)

@app.route('/admin/categories', methods=['GET'])
@require_co_admin
def admin_get_categories():
    """Haal alle categorieën op"""
    return jsonify(load_server_categories())

@app.route('/admin/categories', methods=['POST'])
@require_co_admin
def admin_add_category():
    """Voeg categorie toe"""
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Naam is vereist'}), 400

    categories = load_server_categories()
    if any(c.get('name') == name for c in categories):
        return jsonify({'error': 'Categorie bestaat al'}), 400

    categories.append({
        'name': name,
        'image_url': '',
        'show_image': False,
        'software': '',
        'version': ''
    })
    if save_server_categories(categories):
        return jsonify({'success': True})
    return jsonify({'error': 'Fout bij opslaan'}), 500

@app.route('/admin/categories/<name>', methods=['PUT'])
@require_co_admin
def admin_update_category(name):
    """Hernoem categorie"""
    data = request.get_json()
    new_name = data.get('new_name')
    image_url = data.get('image_url')
    show_image = data.get('show_image')
    software = data.get('software')
    version = data.get('version')

    categories = load_server_categories()

    category_to_update = next((c for c in categories if c.get('name') == name), None)
    if not category_to_update:
        return jsonify({'error': 'Categorie niet gevonden'}), 404

    if new_name and new_name != name:
        if any(c.get('name') == new_name for c in categories):
            return jsonify({'error': 'Categorie naam bestaat al'}), 400
        category_to_update['name'] = new_name

    if image_url is not None:
        category_to_update['image_url'] = image_url

    if show_image is not None:
        category_to_update['show_image'] = show_image

    if software is not None:
        category_to_update['software'] = software

    if version is not None:
        category_to_update['version'] = version

    if save_server_categories(categories):
        if new_name and new_name != name:
            plugins = load_plugins()
            updated = False
            for plugin in plugins:
                if plugin.get('category') == name:
                    plugin['category'] = new_name
                    updated = True
            if updated:
                save_plugins(plugins)
        return jsonify({'success': True})
    return jsonify({'error': 'Fout bij opslaan'}), 500

@app.route('/admin/categories/<name>', methods=['DELETE'])
@require_co_admin
def admin_delete_category(name):
    """Verwijder categorie"""
    categories = load_server_categories()

    original_count = len(categories)
    categories = [c for c in categories if c.get('name') != name]

    if len(categories) == original_count:
        return jsonify({'error': 'Categorie niet gevonden'}), 404

    if save_server_categories(categories):
        return jsonify({'success': True})
    return jsonify({'error': 'Fout bij opslaan'}), 500

@app.route('/admin/users/<username>', methods=['DELETE'])
@require_admin
def admin_delete_user(username):
    """Verwijder gebruiker"""
    if username == 'admin':
        return jsonify({'error': 'Admin kan niet verwijderd worden'}), 400
        
    users = load_users()
    users = [u for u in users if u['username'] != username]
    
    if save_users(users):
        return jsonify({'success': True})
    return jsonify({'error': 'Fout bij verwijderen'}), 500

@app.route('/admin/settings', methods=['GET'])
@require_admin
def admin_get_settings():
    """Haal instellingen op"""
    return jsonify(load_settings())

@app.route('/admin/settings', methods=['POST'])
@require_co_admin
def admin_update_settings():
    """Update instellingen"""
    data = request.get_json()
    if save_settings(data):
        return jsonify({'success': True})
    return jsonify({'error': 'Fout bij opslaan'}), 500

@app.route('/admin/users/<username>/role', methods=['POST'])
@require_admin
def admin_change_role(username):
    """Wijzig gebruikersrol"""
    data = request.get_json()
    new_role = data.get('role')
    
    if new_role not in ['user', 'co-admin', 'admin']:
        return jsonify({'error': 'Ongeldige rol'}), 400
    
    users = load_users()
    user = next((u for u in users if u['username'] == username), None)
    
    if not user:
        return jsonify({'error': 'Gebruiker niet gevonden'}), 404
    
    user['role'] = new_role
    
    if save_users(users):
        return jsonify({'success': True})
    return jsonify({'error': 'Fout bij opslaan'}), 500

@app.route('/admin/plugins', methods=['GET'])
@require_co_admin
def admin_get_plugins():
    """Haal alle plugins op"""
    return jsonify(load_plugins())

@app.route('/admin/plugins/<path:url>', methods=['DELETE'])
@require_co_admin
def admin_delete_plugin(url):
    """Verwijder plugin (admin)"""
    if delete_any_plugin(url):
        return jsonify({'success': True})
    return jsonify({'error': 'Plugin niet gevonden'}), 404

@app.route('/admin/plugins/<path:url>/details', methods=['POST'])
@require_co_admin
def admin_update_plugin_details(url):
    """Update plugin details (title, author, category)"""
    try:
        data = request.get_json()
        new_title = data.get('title')
        new_author = data.get('author')
        new_category = data.get('category')

        if not new_title or not new_author:
            return jsonify({'error': 'Titel en auteur zijn vereist'}), 400

        plugins = load_plugins()
        plugin_found = False
        for plugin in plugins:
            if plugin.get('url') == url:
                plugin['title'] = new_title
                plugin['author'] = new_author
                if new_category is not None:
                    plugin['category'] = new_category
                plugin_found = True
                break
        
        if plugin_found:
            if save_plugins(plugins):
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Fout bij opslaan van plugin details'}), 500
        else:
            return jsonify({'error': 'Plugin niet gevonden'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/fetch_plugin', methods=['POST'])
def fetch_plugin():
    """Haal plugin data op voor een gegeven URL"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'Geen URL opgegeven'}), 400
        
        # Voer launcher.py uit om plugin data op te halen
        result = subprocess.run(
            [sys.executable, 'launcher.py', url],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse de JSON output
        plugin_data = json_module.loads(result.stdout)
        return jsonify(plugin_data)
        
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Fout bij ophalen plugin data: {e.stderr}'}), 500
    except Exception as e:
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500

@app.route('/add_plugin', methods=['POST'])
@require_login
def add_plugin():
    """Voeg een plugin toe aan de repository"""
    try:
        data = request.get_json()
        plugin_data = data.get('plugin_data')
        
        if not plugin_data:
            return jsonify({'error': 'Geen plugin data opgegeven'}), 400
        
        username = session['user']
        
        if add_user_plugin(username, plugin_data):
            return jsonify({'success': True, 'message': 'Plugin succesvol toegevoegd'})
        else:
            return jsonify({'error': 'Fout bij opslaan plugin'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500

@app.route('/delete_plugin', methods=['POST'])
@require_login
def delete_plugin():
    """Verwijder een plugin uit de repository"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'Geen URL opgegeven'}), 400
        
        username = session['user']
        user = get_current_user()
        
        # Admin en co-admin kunnen elke plugin verwijderen
        if user and user.get('role') in ['admin', 'co-admin']:
            if delete_any_plugin(url):
                return jsonify({'success': True, 'message': 'Plugin succesvol verwijderd'})
        # Normale gebruikers kunnen alleen hun eigen plugins verwijderen
        elif delete_user_plugin(username, url):
            return jsonify({'success': True, 'message': 'Plugin succesvol verwijderd'})
        
        return jsonify({'error': 'Plugin niet gevonden of fout bij verwijderen'}), 404
        
    except Exception as e:
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)