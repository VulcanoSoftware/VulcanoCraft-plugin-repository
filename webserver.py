from flask import Flask, jsonify, request, send_file, session
import os
import subprocess
import sys
import hashlib
import secrets
from bson import json_util
from database import (
    get_plugins_collection,
    get_users_collection,
    get_server_categories_collection,
    get_settings_collection,
    get_loaders_collection
)
import json as json_module

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Helper to serialize MongoDB ObjectId
def mongo_jsonify(data):
    """Serialiseert MongoDB data, inclusief ObjectId's, naar een JSON-string."""
    return json_module.loads(json_util.dumps(data))

# --- Data Functies ---

def get_all_plugins():
    """Haal alle plugins op uit de database."""
    plugins_collection = get_plugins_collection()
    return list(plugins_collection.find())

def get_user_plugins(username):
    """Haal plugins van een specifieke gebruiker op."""
    plugins_collection = get_plugins_collection()
    return list(plugins_collection.find({'owner': username}))

def add_user_plugin(username, plugin_data):
    """Voeg een plugin toe of werk deze bij voor een specifieke gebruiker."""
    plugins_collection = get_plugins_collection()
    plugin_data['owner'] = username
    # Gebruik 'url' als unieke sleutel voor de update/insert (upsert) operatie
    result = plugins_collection.update_one(
        {'url': plugin_data['url']},
        {'$set': plugin_data},
        upsert=True
    )
    return result.acknowledged

def delete_user_plugin(username, url):
    """Verwijder een plugin van een specifieke gebruiker."""
    plugins_collection = get_plugins_collection()
    result = plugins_collection.delete_one({'url': url, 'owner': username})
    return result.deleted_count > 0

def delete_any_plugin(url):
    """Verwijder een plugin (admin functie)."""
    plugins_collection = get_plugins_collection()
    result = plugins_collection.delete_one({'url': url})
    return result.deleted_count > 0

def get_all_users():
    """Haal alle gebruikers op uit de database."""
    users_collection = get_users_collection()
    return list(users_collection.find())

def hash_password(password):
    """Hash een wachtwoord met SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def get_current_user():
    """Haal de momenteel ingelogde gebruiker op."""
    if 'user' not in session:
        return None
    users_collection = get_users_collection()
    return users_collection.find_one({'username': session['user']})

def load_settings():
    """Laad de applicatie-instellingen uit de database."""
    settings_collection = get_settings_collection()
    settings = settings_collection.find_one()
    # Zorg voor een standaardwaarde als de database leeg is
    return settings if settings else {'registration_enabled': True}

def save_settings(settings_data):
    """Sla de applicatie-instellingen op in de database."""
    settings_collection = get_settings_collection()
    # Er is slechts één instellingendocument, dus voer een upsert uit
    result = settings_collection.update_one(
        {},
        {'$set': settings_data},
        upsert=True
    )
    return result.acknowledged

def load_server_categories():
    """Laad servercategorieën uit de database."""
    categories_collection = get_server_categories_collection()
    return list(categories_collection.find())

# --- Decorators ---

def require_login(f):
    """Decorator die controleert of een gebruiker is ingelogd."""
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Login vereist'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def require_admin(f):
    """Decorator die controleert of een gebruiker admin-rechten heeft."""
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin rechten vereist'}), 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def require_co_admin(f):
    """Decorator die controleert of een gebruiker co-admin of admin rechten heeft."""
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user.get('role') not in ['admin', 'co-admin']:
            return jsonify({'error': 'Co-Admin rechten vereist'}), 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# --- Routes (Statische Bestanden & Pagina's) ---

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/login-page')
def login_page():
    return send_file('components/user/login.html')

@app.route('/change_password', methods=['GET', 'POST'])
def change_password_page():
    return send_file('components/user/change_password.html')

@app.route('/style.css')
def serve_css():
    return send_file('style.css', mimetype='text/css')

@app.route('/script.js')
def serve_js():
    return send_file('script.js', mimetype='application/javascript')

@app.route('/js/<path:filename>')
def serve_js_from_folder(filename):
    return send_file(f'js/{filename}', mimetype='application/javascript')

@app.route('/css/<path:filename>')
def serve_css_from_folder(filename):
    return send_file(f'css/{filename}', mimetype='text/css')

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_file(f'images/{filename}')

# --- API Routes (Publiek) ---

@app.route('/api/plugins/public')
def api_plugins_public():
    """API endpoint voor alle plugin-data (publiek toegankelijk)."""
    plugins = get_all_plugins()
    return jsonify(mongo_jsonify(plugins))

@app.route('/api/server_categories')
def api_server_categories():
    """API endpoint voor servercategorieën."""
    categories = load_server_categories()
    return jsonify(mongo_jsonify(categories))

@app.route('/api/server_info')
def api_server_info():
    """API endpoint voor server software en versie-info per categorie."""
    categories = load_server_categories()
    server_info = {
        cat.get('name'): {
            'software': cat.get('software', ''),
            'version': cat.get('version', '')
        } for cat in categories if 'name' in cat
    }
    return jsonify(server_info)

@app.route('/api/loaders')
def api_loaders():
    """API endpoint voor loader-data."""
    loaders_collection = get_loaders_collection()
    loaders = list(loaders_collection.find())
    return jsonify(mongo_jsonify(loaders))

@app.route('/registration-status')
def registration_status():
    """Controleert of registratie is ingeschakeld."""
    settings = load_settings()
    return jsonify({'enabled': settings.get('registration_enabled', True)})

# --- API Routes (Authenticatie) ---

@app.route('/register', methods=['POST'])
def register():
    """Registreer een nieuwe gebruiker."""
    settings = load_settings()
    if not settings.get('registration_enabled', True):
        return jsonify({'error': 'Registratie is uitgeschakeld'}), 403
        
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Gebruikersnaam en wachtwoord zijn vereist'}), 400

    users_collection = get_users_collection()
    if users_collection.find_one({'username': username}):
        return jsonify({'error': 'Gebruikersnaam bestaat al'}), 400

    users_collection.insert_one({
        'username': username,
        'password': hash_password(password),
        'role': 'user'
    })
    return jsonify({'success': True})

@app.route('/login', methods=['POST'])
def login():
    """Log een gebruiker in."""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Gebruikersnaam en wachtwoord vereist'}), 400

    users_collection = get_users_collection()
    user = users_collection.find_one({
        'username': username,
        'password': hash_password(password)
    })

    if user:
        session['user'] = user['username']
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Ongeldige inloggegevens'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    """Log een gebruiker uit."""
    session.pop('user', None)
    return jsonify({'success': True})

@app.route('/auth-status')
def auth_status():
    """Controleer de inlogstatus."""
    user = get_current_user()
    return jsonify({
        'logged_in': 'user' in session,
        'username': session.get('user'),
        'role': user.get('role', 'user') if user else 'user'
    })

# --- API Routes (Gebruikersacties - Ingelogd) ---

@app.route('/api/plugins')
@require_login
def api_plugins():
    """API endpoint voor plugin-data van de ingelogde gebruiker."""
    plugins = get_user_plugins(session['user'])
    return jsonify(mongo_jsonify(plugins))

@app.route('/api/change-password', methods=['POST'])
@require_login
def change_password():
    """Wijzig het wachtwoord van de ingelogde gebruiker."""
    data = request.get_json()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return jsonify({'error': 'Oud en nieuw wachtwoord zijn vereist'}), 400

    user = get_current_user()
    if not user:
        return jsonify({'error': 'Gebruiker niet ingelogd'}), 401

    if hash_password(old_password) != user['password']:
        return jsonify({'error': 'Oud wachtwoord is onjuist'}), 401

    users_collection = get_users_collection()
    users_collection.update_one(
        {'username': user['username']},
        {'$set': {'password': hash_password(new_password)}}
    )
    return jsonify({'success': True, 'message': 'Wachtwoord succesvol gewijzigd'})

@app.route('/fetch_plugin', methods=['POST'])
def fetch_plugin():
    """Haal plugin-data op voor een gegeven URL via launcher.py."""
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'Geen URL opgegeven'}), 400

    try:
        result = subprocess.run(
            [sys.executable, 'launcher.py', url],
            capture_output=True, text=True, check=True
        )
        plugin_data = json_module.loads(result.stdout)
        return jsonify(plugin_data)
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Fout bij ophalen plugin data: {e.stderr}'}), 500
    except Exception as e:
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500

@app.route('/add_plugin', methods=['POST'])
@require_login
def add_plugin():
    """Voeg een plugin toe aan de repository."""
    data = request.get_json()
    plugin_data = data.get('plugin_data')
    if not plugin_data:
        return jsonify({'error': 'Geen plugin data opgegeven'}), 400

    if add_user_plugin(session['user'], plugin_data):
        return jsonify({'success': True, 'message': 'Plugin succesvol toegevoegd'})
    else:
        return jsonify({'error': 'Fout bij opslaan plugin'}), 500

@app.route('/delete_plugin', methods=['POST'])
@require_login
def delete_plugin():
    """Verwijder een plugin uit de repository."""
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'Geen URL opgegeven'}), 400

    user = get_current_user()
    # Admins en co-admins kunnen elke plugin verwijderen
    if user and user.get('role') in ['admin', 'co-admin']:
        if delete_any_plugin(url):
            return jsonify({'success': True, 'message': 'Plugin succesvol verwijderd'})
    # Normale gebruikers kunnen alleen hun eigen plugins verwijderen
    elif delete_user_plugin(session['user'], url):
        return jsonify({'success': True, 'message': 'Plugin succesvol verwijderd'})

    return jsonify({'error': 'Plugin niet gevonden of fout bij verwijderen'}), 404

# --- Admin Routes ---

@app.route('/admin')
def admin_panel():
    return send_file('components/admin/admin.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    users_collection = get_users_collection()
    user = users_collection.find_one({
        'username': username,
        'password': hash_password(password)
    })
    
    if user and user.get('role') in ['admin', 'co-admin']:
        session['user'] = username
        return jsonify({'success': True, 'role': user.get('role')})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/admin/check-session')
def admin_check_session():
    """Controleer de admin-sessiestatus."""
    user = get_current_user()
    if user and user.get('role') in ['admin', 'co-admin']:
        return jsonify({
            'logged_in': True,
            'role': user.get('role'),
            'username': user.get('username')
        })
    return jsonify({'logged_in': False})

@app.route('/admin/users', methods=['GET'])
@require_co_admin
def admin_get_users():
    """Haal alle gebruikers op met het aantal plugins dat ze bezitten."""
    users = get_all_users()
    plugins_collection = get_plugins_collection()
    
    # Gebruik een aggregation pipeline om efficiënt het aantal plugins per gebruiker te tellen
    pipeline = [
        {"$group": {"_id": "$owner", "count": {"$sum": 1}}}
    ]
    plugin_counts = {item['_id']: item['count'] for item in plugins_collection.aggregate(pipeline)}

    user_data = [{
        'username': u['username'],
        'role': u.get('role', 'user'),
        'plugin_count': plugin_counts.get(u['username'], 0)
    } for u in users]

    return jsonify(mongo_jsonify(user_data))

@app.route('/admin/users/<username>', methods=['DELETE'])
@require_admin
def admin_delete_user(username):
    """Verwijder een gebruiker."""
    if username == 'admin':
        return jsonify({'error': 'De admin-gebruiker kan niet worden verwijderd'}), 400

    users_collection = get_users_collection()
    result = users_collection.delete_one({'username': username})

    if result.deleted_count > 0:
        return jsonify({'success': True})
    return jsonify({'error': 'Fout bij verwijderen'}), 500

@app.route('/admin/users/<username>/role', methods=['POST'])
@require_admin
def admin_change_role(username):
    """Wijzig de rol van een gebruiker."""
    data = request.get_json()
    new_role = data.get('role')

    if new_role not in ['user', 'co-admin', 'admin']:
        return jsonify({'error': 'Ongeldige rol'}), 400
    
    users_collection = get_users_collection()
    result = users_collection.update_one(
        {'username': username},
        {'$set': {'role': new_role}}
    )

    if result.modified_count > 0:
        return jsonify({'success': True})
    return jsonify({'error': 'Gebruiker niet gevonden of rol is ongewijzigd'}), 404

@app.route('/admin/settings', methods=['GET'])
@require_admin
def admin_get_settings():
    """Haal de applicatie-instellingen op."""
    return jsonify(mongo_jsonify(load_settings()))

@app.route('/admin/settings', methods=['POST'])
@require_co_admin
def admin_update_settings():
    """Werk de applicatie-instellingen bij."""
    if save_settings(request.get_json()):
        return jsonify({'success': True})
    return jsonify({'error': 'Fout bij opslaan'}), 500

@app.route('/admin/categories', methods=['GET'])
@require_co_admin
def admin_get_categories():
    """Haal alle categorieën op."""
    return jsonify(mongo_jsonify(load_server_categories()))

@app.route('/admin/categories', methods=['POST'])
@require_co_admin
def admin_add_category():
    """Voeg een nieuwe categorie toe."""
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Naam is vereist'}), 400

    categories_collection = get_server_categories_collection()
    if categories_collection.find_one({'name': name}):
        return jsonify({'error': 'Categorie bestaat al'}), 400

    categories_collection.insert_one({
        'name': name, 'image_url': '', 'show_image': False,
        'software': '', 'version': ''
    })
    return jsonify({'success': True})

@app.route('/admin/categories/<name>', methods=['PUT'])
@require_co_admin
def admin_update_category(name):
    """Werk een bestaande categorie bij."""
    data = request.get_json()
    categories_collection = get_server_categories_collection()

    update_fields = {}
    if 'image_url' in data: update_fields['image_url'] = data['image_url']
    if 'show_image' in data: update_fields['show_image'] = data['show_image']
    if 'software' in data: update_fields['software'] = data['software']
    if 'version' in data: update_fields['version'] = data['version']
    if 'new_name' in data and data['new_name'] != name:
        new_name = data['new_name']
        if categories_collection.find_one({'name': new_name}):
            return jsonify({'error': 'Categorienaam bestaat al'}), 400
        update_fields['name'] = new_name

    result = categories_collection.update_one({'name': name}, {'$set': update_fields})

    if result.modified_count == 0:
        return jsonify({'error': 'Categorie niet gevonden of geen wijzigingen'}), 404
        
    # Als de naam is gewijzigd, werk dan alle plugins in die categorie bij
    if 'new_name' in data and data['new_name'] != name:
        plugins_collection = get_plugins_collection()
        plugins_collection.update_many(
            {'category': name},
            {'$set': {'category': data['new_name']}}
        )
    
    return jsonify({'success': True})

@app.route('/admin/categories/<name>', methods=['DELETE'])
@require_co_admin
def admin_delete_category(name):
    """Verwijder een categorie."""
    categories_collection = get_server_categories_collection()
    result = categories_collection.delete_one({'name': name})
    if result.deleted_count > 0:
        return jsonify({'success': True})
    return jsonify({'error': 'Categorie niet gevonden'}), 404

@app.route('/admin/plugins', methods=['GET'])
@require_co_admin
def admin_get_plugins():
    """Haal alle plugins op."""
    return jsonify(mongo_jsonify(get_all_plugins()))

@app.route('/admin/plugins/<path:url>', methods=['DELETE'])
@require_co_admin
def admin_delete_plugin(url):
    """Verwijder een plugin (admin)."""
    if delete_any_plugin(url):
        return jsonify({'success': True})
    return jsonify({'error': 'Plugin niet gevonden'}), 404

@app.route('/admin/plugins/<path:url>/details', methods=['POST'])
@require_co_admin
def admin_update_plugin_details(url):
    """Werk plugindetails bij (titel, auteur, categorie)."""
    data = request.get_json()
    update_fields = {
        'title': data.get('title'),
        'author': data.get('author'),
        'category': data.get('category')
    }
    if not update_fields['title'] or not update_fields['author']:
        return jsonify({'error': 'Titel en auteur zijn vereist'}), 400

    plugins_collection = get_plugins_collection()
    result = plugins_collection.update_one({'url': url}, {'$set': update_fields})

    if result.modified_count > 0:
        return jsonify({'success': True})
    return jsonify({'error': 'Plugin niet gevonden of geen wijzigingen'}), 404


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
