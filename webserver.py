from flask import Flask, jsonify, request, send_file, session
import os
import json as json_module
import subprocess
import sys
import hashlib
import secrets
import threading
import time
import shutil
import requests
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Te veel verzoeken. Probeer het later opnieuw.'}), 429
env_name = os.getenv("FLASK_ENV", "development")
secret_key = os.getenv("FLASK_SECRET_KEY")
if env_name == "production" and not secret_key:
    raise RuntimeError("FLASK_SECRET_KEY must be set in production")
app.secret_key = secret_key or secrets.token_hex(32)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "vulcanocraft")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB_NAME]
db.users.create_index("username", unique=True)

def run_migrations():
    """Voer eventuele databasemigraties uit bij de opstart."""
    try:
        plugins = list(db.plugins.find({}))
        for plugin in plugins:
            updated = False
            set_fields = {}
            if "category" in plugin and "categories" not in plugin:
                cat = plugin["category"]
                set_fields["categories"] = [cat] if cat else []
                updated = True
            elif "categories" in plugin and "category" not in plugin:
                cats = plugin["categories"]
                set_fields["category"] = cats[0] if cats and isinstance(cats, list) else None
                updated = True

            if updated and set_fields:
                db.plugins.update_one({"_id": plugin["_id"]}, {"$set": set_fields})
    except Exception as e:
        print(f"Fout bij uitvoeren van migraties: {e}")

run_migrations()

def load_plugins():
    """Laad de plugins data"""
    try:
        docs = list(db.plugins.find({}))
        plugins = []
        for doc in docs:
            obj_id = doc.pop("_id", None)
            if obj_id and hasattr(obj_id, "generation_time"):
                gen_iso = obj_id.generation_time.isoformat()
                doc.setdefault("created_at", gen_iso)
                doc.setdefault("added_at", gen_iso)
                doc.setdefault("updated_at", gen_iso)
                doc.setdefault("last_modified", gen_iso)
            plugins.append(doc)
        return plugins
    except Exception as e:
        print(f"Fout bij het laden van plugins: {e}")
        return []
    
def save_plugins(plugins):
    """Sla plugins op in de database"""
    try:
        if not isinstance(plugins, list):
            return False
        db.plugins.delete_many({})
        if plugins:
            db.plugins.insert_many(plugins)
        return True
    except Exception as e:
        print(f"Fout bij het opslaan van plugins: {e}")
        return False

def get_user_plugins(username):
    """Haal plugins van specifieke gebruiker op"""
    try:
        return list(db.plugins.find({"owner": username}, {"_id": 0}))
    except Exception as e:
        print(f"Fout bij het laden van plugins voor gebruiker: {e}")
        return []

def add_user_plugin(username, plugin_data):
    """Voeg plugin toe voor specifieke gebruiker"""
    try:
        plugin_data = dict(plugin_data or {})
        plugin_data["owner"] = username

        url = plugin_data.get("url")
        if not url:
            return False

        new_category = plugin_data.get("category")

        existing_plugin = db.plugins.find_one({"url": url, "owner": username})

        if existing_plugin:
            categories = existing_plugin.get("categories")
            if not isinstance(categories, list):
                categories = []

            existing_primary_category = existing_plugin.get("category")
            if existing_primary_category and existing_primary_category not in categories:
                categories.append(existing_primary_category)

            if new_category and new_category not in categories:
                categories.append(new_category)

            if categories:
                plugin_data["categories"] = categories
                plugin_data["category"] = categories[0]

            db.plugins.update_one({"_id": existing_plugin["_id"]}, {"$set": plugin_data})
        else:
            if new_category:
                plugin_data.setdefault("categories", [])
                if new_category not in plugin_data["categories"]:
                    plugin_data["categories"].append(new_category)

            db.plugins.insert_one(plugin_data)

        return True
    except Exception as e:
        print(f"Fout bij het toevoegen van plugin: {e}")
        return False

def delete_user_plugin(username, url):
    """Verwijder plugin van specifieke gebruiker"""
    try:
        result = db.plugins.delete_many({"url": url, "owner": username})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Fout bij verwijderen plugin voor gebruiker: {e}")
        return False

def remove_user_plugin_category(username, url, category):
    """Verwijder een categorie-koppeling van een plugin voor een specifieke gebruiker"""
    try:
        plugin = db.plugins.find_one({"url": url, "owner": username})
        if not plugin:
            return False

        categories = plugin.get("categories")
        if isinstance(categories, list):
            categories = [c for c in categories if c != category]
        else:
            categories = []

        primary_category = plugin.get("category")
        if primary_category == category and categories:
            primary_category = categories[0]
        elif primary_category == category and not categories:
            primary_category = None

        if not categories and not primary_category:
            result = db.plugins.delete_one({"_id": plugin["_id"]})
            return result.deleted_count > 0

        update_data = {
            "categories": categories,
            "category": primary_category
        }

        result = db.plugins.update_one({"_id": plugin["_id"]}, {"$set": update_data})
        return result.modified_count > 0
    except Exception as e:
        print(f"Fout bij verwijderen categorie voor plugin: {e}")
        return False

def delete_any_plugin(url):
    """Verwijder plugin (admin functie)"""
    try:
        result = db.plugins.delete_many({"url": url})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Fout bij verwijderen plugin: {e}")
        return False

def load_users():
    """Laad gebruikers"""
    try:
        users = list(db.users.find({}, {"_id": 0}))
        return users
    except Exception:
        return []
    
def save_users(users):
    """Sla gebruikers op"""
    try:
        if not isinstance(users, list):
            return False
        db.users.delete_many({})
        if users:
            db.users.insert_many(users)
        return True
    except Exception:
        return False

def sanitize_str(val):
    """Ensure value is strictly a string to prevent NoSQL injection."""
    if not isinstance(val, str):
        return ""
    return val.strip()

def sanitize_nosql(val):
    """Recursively strip dicts containing MongoDB query operators ($) or dot notation to prevent NoSQL injection."""
    if isinstance(val, dict):
        return {str(k): sanitize_nosql(v) for k, v in val.items() if not str(k).startswith('$') and '.' not in str(k)}
    elif isinstance(val, list):
        return [sanitize_nosql(v) for v in val]
    return val

ph = PasswordHasher()

def hash_password(password):
    """Hash wachtwoord met Argon2"""
    return ph.hash(password)

def verify_password(stored_hash, password):
    """Verifieer wachtwoord (Argon2 of legacy SHA-256).

    Returns: (is_valid: bool, needs_rehash: bool)
    """
    if not stored_hash or not password:
        return False, False

    if stored_hash.startswith("$argon2"):
        try:
            ph.verify(stored_hash, password)
            needs_rehash = ph.check_needs_rehash(stored_hash)
            return True, needs_rehash
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False, False
    else:
        # Legacy SHA-256 check
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()
        if legacy_hash == stored_hash:
            return True, True
        return False, False

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
        doc = db.settings.find_one({"_id": "app_settings"})
        if doc:
            doc.pop("_id", None)
            return doc
        return {'registration_enabled': True}
    except Exception:
        return {'registration_enabled': True}
    
def save_settings(settings):
    """Sla instellingen op"""
    try:
        if not isinstance(settings, dict):
            return False
        db.settings.update_one({"_id": "app_settings"}, {"$set": settings}, upsert=True)
        return True
    except Exception:
        return False

def load_server_categories():
    """Laad server categorieën"""
    try:
        categories = list(db.server_categories.find({}, {"_id": 0}))
        return categories
    except Exception:
        return []
    
def save_server_categories(categories):
    """Sla server categorieën op"""
    try:
        if not isinstance(categories, list):
            return False
        db.server_categories.delete_many({})
        if categories:
            db.server_categories.insert_many(categories)
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

def get_platform_from_url(url):
    if not url:
        return 'unknown'
    if 'hangar.papermc.io' in url:
        return 'hangar'
    if 'spigotmc.org' in url:
        return 'spigot'
    if 'modrinth.com' in url:
        return 'modrinth'
    if 'dev.bukkit.org' in url:
        return 'bukkitdev'
    if 'github.com' in url:
        return 'github'
    if 'curseforge.com' in url:
        return 'curseforge'
    if 'planetminecraft.com' in url:
        return 'planetminecraft'
    return 'unknown'

def extract_plugin_categories(plugin):
    cats = plugin.get('categories') or ([plugin.get('category')] if plugin.get('category') else []) or plugin.get('tags') or []
    return set(c for c in cats if c)

def compute_plugin_metadata(all_plugins):
    version_set = set()
    loader_set = set()
    category_counts = {}

    server_cats = load_server_categories()
    if isinstance(server_cats, list):
        for sc in server_cats:
            sc_name = sc.get('name') if isinstance(sc, dict) else sc
            if sc_name:
                category_counts[sc_name] = 0

    for plugin in all_plugins:
        v_str = plugin.get('versions', '') or ''
        for ver in v_str.split():
            if ver:
                version_set.add(ver)

        for loader in plugin.get('loaders', []) or []:
            if loader:
                loader_set.add(loader)

        for cat in extract_plugin_categories(plugin):
            category_counts[cat] = category_counts.get(cat, 0) + 1

    return list(version_set), list(loader_set), category_counts

def _check_include_mode(matches_search, search_term, matches_version, selected_version, plugin_platform, selected_platforms, platforms_provided, plugin_loaders, selected_loaders, loaders_provided, matches_category, selected_category):
    if search_term and not matches_search:
        return False
    if selected_version and not matches_version:
        return False
    if selected_category and not matches_category:
        return False
    if platforms_provided:
        if not selected_platforms or plugin_platform not in selected_platforms:
            return False
    if loaders_provided:
        if not selected_loaders or not any(loader in selected_loaders for loader in plugin_loaders):
            return False
    return True

def matches_plugin_criteria(plugin, search_term, selected_version, selected_platforms, selected_loaders, selected_category):
    """Legacy helper function maintained for backwards compatibility."""
    return is_plugin_included(plugin, search_term, selected_version, selected_platforms, selected_loaders, selected_category, include=True)

def is_plugin_included(plugin, search_term, selected_version, selected_platforms, selected_loaders, selected_category, include, all_platforms=None, all_loaders=None, platforms_provided=None, loaders_provided=None):
    if all_platforms is None:
        all_platforms = ['hangar', 'spigot', 'modrinth', 'curseforge', 'bukkitdev', 'github', 'planetminecraft']

    if platforms_provided is None:
        platforms_provided = selected_platforms is not None
    if loaders_provided is None:
        loaders_provided = selected_loaders is not None

    if selected_platforms is None:
        selected_platforms = []
    if selected_loaders is None:
        selected_loaders = []

    title = (plugin.get('title') or '').lower()
    description = (plugin.get('description') or '').lower()
    author = (plugin.get('author') or '').lower()

    matches_search = bool(search_term) and (search_term in title or search_term in description or search_term in author)

    v_str = plugin.get('versions') or ''
    matches_version = bool(selected_version) and (selected_version in v_str.split())

    plugin_platform = get_platform_from_url(plugin.get('url', ''))
    plugin_loaders = plugin.get('loaders') or []
    plugin_cats = extract_plugin_categories(plugin)
    matches_category = bool(selected_category) and (selected_category in plugin_cats)

    included = _check_include_mode(
        matches_search, search_term, matches_version, selected_version,
        plugin_platform, selected_platforms, platforms_provided,
        plugin_loaders, selected_loaders, loaders_provided,
        matches_category, selected_category
    )

    return included if include else not included

def sort_plugins(plugins, sort_by):
    if sort_by == 'name_asc':
        return sorted(plugins, key=lambda p: (p.get('title') or '').lower())
    elif sort_by == 'name_desc':
        return sorted(plugins, key=lambda p: (p.get('title') or '').lower(), reverse=True)
    elif sort_by == 'platform_asc':
        return sorted(plugins, key=lambda p: (get_platform_from_url(p.get('url', '')), (p.get('title') or '').lower()))
    elif sort_by == 'platform_desc':
        return sorted(plugins, key=lambda p: (get_platform_from_url(p.get('url', '')), (p.get('title') or '').lower()), reverse=True)
    elif sort_by == 'updated_asc':
        return sorted(plugins, key=lambda p: (str(p.get('last_modified') or p.get('updated_at') or p.get('created_at') or ''), (p.get('title') or '').lower()))
    elif sort_by == 'updated_desc':
        return sorted(plugins, key=lambda p: (str(p.get('last_modified') or p.get('updated_at') or p.get('created_at') or ''), (p.get('title') or '').lower()), reverse=True)
    elif sort_by == 'added_asc':
        return sorted(plugins, key=lambda p: (str(p.get('created_at') or p.get('added_at') or ''), (p.get('title') or '').lower()))
    elif sort_by == 'added_desc':
        return sorted(plugins, key=lambda p: (str(p.get('created_at') or p.get('added_at') or ''), (p.get('title') or '').lower()), reverse=True)
    return plugins

def expand_plugin_categories(per_plugin_filtered, selected_category):
    filtered_expanded = []
    if not selected_category:
        for plugin in per_plugin_filtered:
            plugin_cats = list(extract_plugin_categories(plugin))
            if not plugin_cats:
                p_copy = dict(plugin)
                p_copy['_categoryContext'] = ''
                filtered_expanded.append(p_copy)
            else:
                for cat in plugin_cats:
                    p_copy = dict(plugin)
                    p_copy['_categoryContext'] = cat
                    filtered_expanded.append(p_copy)
    else:
        for plugin in per_plugin_filtered:
            p_copy = dict(plugin)
            p_copy['_categoryContext'] = selected_category
            filtered_expanded.append(p_copy)

    return filtered_expanded

def paginate_items(items, page, per_page):
    total_items = len(items)
    if per_page <= 0:
        return items, total_items, 1, 1

    total_pages = max(1, (total_items + per_page - 1) // per_page)
    current_page = max(1, min(page, total_pages)) if total_pages > 0 else 1
    start_idx = (current_page - 1) * per_page
    end_idx = start_idx + per_page

    return items[start_idx:end_idx], total_items, current_page, total_pages

def parse_public_api_params(req):
    """Helper om de query parameters van de public API request te parsen."""
    platforms_provided = 'platforms' in req.args
    loaders_provided = 'loaders' in req.args

    platforms_raw = req.args.get('platforms', '')
    loaders_raw = req.args.get('loaders', '')
    return {
        'page': req.args.get('page', 1, type=int),
        'per_page': req.args.get('per_page', 20, type=int),
        'search_term': req.args.get('search', '').lower().strip(),
        'selected_version': req.args.get('version', ''),
        'selected_platforms': [p.strip() for p in platforms_raw.split(',') if p.strip()] if platforms_raw else [],
        'platforms_provided': platforms_provided,
        'selected_loaders': [loader.strip() for loader in loaders_raw.split(',') if loader.strip()] if loaders_raw else [],
        'loaders_provided': loaders_provided,
        'selected_category': req.args.get('category', ''),
        'include': req.args.get('include', 'true').lower() != 'false',
        'sort_by': req.args.get('sort', 'name_asc')
    }

@app.route('/api/plugins/public')
def api_plugins_public():
    """API endpoint voor alle plugins data met filtering en paginering"""
    all_plugins = load_plugins()
    params = parse_public_api_params(request)

    all_versions, all_loaders, category_counts = compute_plugin_metadata(all_plugins)
    ALL_PLATFORMS = ['hangar', 'spigot', 'modrinth', 'curseforge', 'bukkitdev', 'github', 'planetminecraft']

    per_plugin_filtered = [
        plugin for plugin in all_plugins
        if is_plugin_included(
            plugin,
            params['search_term'],
            params['selected_version'],
            params['selected_platforms'],
            params['selected_loaders'],
            params['selected_category'],
            params['include'],
            ALL_PLATFORMS,
            all_loaders,
            params['platforms_provided'],
            params['loaders_provided']
        )
    ]

    per_plugin_filtered = sort_plugins(per_plugin_filtered, params['sort_by'])
    filtered_expanded = expand_plugin_categories(per_plugin_filtered, params['selected_category'])
    paginated_plugins, total_items, current_page, total_pages = paginate_items(
        filtered_expanded, params['page'], params['per_page']
    )

    return jsonify({
        'plugins': paginated_plugins,
        'total': total_items,
        'total_all': len(all_plugins),
        'page': current_page,
        'per_page': params['per_page'],
        'total_pages': total_pages,
        'all_versions': all_versions,
        'all_loaders': all_loaders,
        'category_counts': category_counts
    })


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
        loaders = list(db.loaders.find({}, {"_id": 0}))
        return jsonify(loaders)
    except Exception as e:
        print(f"Fout bij het laden van loaders: {e}")
        return jsonify({'error': 'Fout bij het laden van loaders'}), 500

@app.route('/register', methods=['POST'])
@limiter.limit("10 per minute")
def register():
    """Registreer nieuwe gebruiker"""
    try:
        settings = load_settings()
        if not settings.get('registration_enabled', True):
            return jsonify({'error': 'Registratie is uitgeschakeld'}), 403
            
        data = request.get_json() or {}
        username = sanitize_str(data.get('username', ''))
        raw_password = data.get('password', '')
        password = raw_password if isinstance(raw_password, str) else ''
        
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
@limiter.limit("10 per minute")
def login():
    """Login gebruiker"""
    try:
        data = request.get_json() or {}
        username = sanitize_str(data.get('username', ''))
        raw_password = data.get('password', '')
        password = raw_password if isinstance(raw_password, str) else ''
        
        if not username or not password:
            return jsonify({'error': 'Gebruikersnaam en wachtwoord vereist'}), 400
        
        users = load_users()
        user = next((u for u in users if u['username'] == username), None)
        
        if user:
            is_valid, needs_rehash = verify_password(user.get('password', ''), password)
            if is_valid:
                if needs_rehash:
                    new_hash = hash_password(password)
                    db.users.update_one({"username": username}, {"$set": {"password": new_hash}})
                session['user'] = user['username']
                return jsonify({'success': True})

        return jsonify({'error': 'Ongeldige inloggegevens'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout', methods=['POST'])
def logout():
    """Logout gebruiker"""
    session.pop('user', None)
    return jsonify({'success': True})

@app.route('/api/change-password', methods=['POST'])
@limiter.limit("10 per minute")
@require_login
def change_password():
    """Wijzig het wachtwoord van de ingelogde gebruiker"""
    try:
        data = request.get_json() or {}
        raw_old = data.get('old_password', '')
        raw_new = data.get('new_password', '')
        old_password = raw_old if isinstance(raw_old, str) else ''
        new_password = raw_new if isinstance(raw_new, str) else ''

        if not old_password or not new_password:
            return jsonify({'error': 'Oud en nieuw wachtwoord zijn vereist'}), 400

        user = get_current_user()
        if not user:
            return jsonify({'error': 'Gebruiker niet ingelogd'}), 401

        # Controleer of het oude wachtwoord correct is
        is_valid, _ = verify_password(user.get('password', ''), old_password)
        if not is_valid:
            return jsonify({'error': 'Oud wachtwoord is onjuist'}), 401

        # Update het wachtwoord met nieuw Argon2 hash
        new_hash = hash_password(new_password)
        result = db.users.update_one({"username": user['username']}, {"$set": {"password": new_hash}})
        if result.modified_count > 0 or result.matched_count > 0:
            return jsonify({'success': True, 'message': 'Wachtwoord succesvol gewijzigd'})
        else:
            return jsonify({'error': 'Fout bij opslaan van nieuw wachtwoord'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def sync_files_to_host(source_dir=".", host_dir="/host"):
    """
    Synchroniseer bijgewerkte bestanden van de container naar de host via de bind mount.

    Veiligheidsregels:
    1. Alleen bestanden die AL BESTAAN op de host worden geüpdatet (geen nieuwe bestanden worden toegevoegd).
    2. Gevoelige of dynamische bestanden en mappen zoals .env, .env.*, MongoDB-data (mongo-live-data),
       backups, .git, .venv en __pycache__ worden strikt genegeerd en ongewijzigd gelaten.
    """
    if not os.path.exists(host_dir):
        print(f"Host directory {host_dir} bestaat niet of is niet gemount. Synchronisatie overgeslagen.")
        return False

    ignored_dirs = {'.git', '.venv', '__pycache__', 'mongo-live-data', 'backups'}

    try:
        for root, dirs, files in os.walk(source_dir):
            # Filter mappen zodat genegeerde mappen niet worden doorzocht
            dirs[:] = [d for d in dirs if d not in ignored_dirs]

            rel_root = os.path.relpath(root, source_dir)
            if rel_root == '.':
                rel_root = ''

            for file_name in files:
                # Bescherm .env en .env.* bestanden tegen overschrijven
                if file_name == '.env' or file_name.startswith('.env.'):
                    continue

                rel_path = os.path.join(rel_root, file_name) if rel_root else file_name
                source_file = os.path.join(root, file_name)
                host_file = os.path.join(host_dir, rel_path)

                # Veiligheidscontrole: update alleen als het bestand al op de host bestaat
                if os.path.isfile(host_file):
                    shutil.copy2(source_file, host_file)
                    print(f"Bestand gesynchroniseerd naar host: {rel_path}")

        return True
    except Exception as e:
        print(f"Fout bij synchroniseren naar host: {e}")
        return False


def _check_github_update(local_sha, headers):
    """Helper function to fetch remote commit info and check update availability."""
    response = requests.get(
        'https://api.github.com/repos/VulcanoSoftware/VulcanoCraft-plugin-repository/commits/main',
        headers=headers,
        timeout=10
    )
    if response.status_code != 200:
        return None, f'Kon GitHub API niet bereiken (Status {response.status_code})'

    remote_data = response.json()
    remote_sha = remote_data.get('sha', '')
    commit_info = remote_data.get('commit', {})
    commit_message = commit_info.get('message', '')
    commit_date = commit_info.get('committer', {}).get('date', '')

    update_available = False
    if remote_sha and local_sha != remote_sha:
        try:
            compare_url = f'https://api.github.com/repos/VulcanoSoftware/VulcanoCraft-plugin-repository/compare/{local_sha}...{remote_sha}'
            comp_resp = requests.get(compare_url, headers=headers, timeout=10)
            if comp_resp.status_code == 200:
                comp_data = comp_resp.json()
                ahead_by = comp_data.get('ahead_by', 0)
                status = comp_data.get('status', '')
                update_available = (ahead_by > 0) or (status in ['ahead', 'diverged'])
            else:
                update_available = True
        except Exception:
            update_available = True

    return {
        'remote_sha': remote_sha,
        'commit_message': commit_message,
        'commit_date': commit_date,
        'update_available': update_available
    }, None

def _get_git_history(local_sha, count=15):
    """Helper function to fetch local git commit history."""
    history = []
    try:
        log_output = subprocess.check_output(
            ['git', 'log', '-n', str(count), '--format=%H|%h|%an|%ad|%s', '--date=iso'],
            text=True
        )
        for line in log_output.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|', 4)
            if len(parts) == 5:
                c_sha, c_short, c_author, c_date, c_msg = parts
                history.append({
                    'sha': c_sha,
                    'short_sha': c_short,
                    'author': c_author,
                    'date': c_date,
                    'message': c_msg,
                    'is_current': (c_sha == local_sha)
                })
    except Exception as log_err:
        print(f"Fout bij ophalen commit geschiedenis: {log_err}")
    return history

def _get_previous_commit(local_sha, history):
    """Helper function to locate the previous commit SHA."""
    previous_sha = ""
    for ref in ['ORIG_HEAD', 'HEAD~1']:
        res = subprocess.run(['git', 'rev-parse', ref], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            candidate = res.stdout.strip()
            if candidate != local_sha:
                previous_sha = candidate
                break

    if not previous_sha and len(history) > 1:
        for item in history:
            if item['sha'] != local_sha:
                previous_sha = item['sha']
                break
    return previous_sha

@app.route('/admin/update/check', methods=['GET'])
@require_admin
def admin_check_update():
    """Controleer of er een update beschikbaar is op GitHub main branch en haal commit historie op."""
    try:
        try:
            local_sha = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                text=True
            ).strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            return jsonify({'error': 'Geen git repository of git executable gevonden op de server.'}), 500

        headers = {'User-Agent': 'VulcanoCraft-Repository-App'}
        remote_info, err = _check_github_update(local_sha, headers)
        if err:
            return jsonify({'error': err}), 502

        history = _get_git_history(local_sha, count=15)
        previous_sha = _get_previous_commit(local_sha, history)

        remote_sha = remote_info['remote_sha']
        return jsonify({
            'update_available': remote_info['update_available'],
            'rollback_available': bool(previous_sha or len(history) > 1),
            'previous_commit': previous_sha[:7] if previous_sha else '',
            'full_previous_commit': previous_sha,
            'current_commit': local_sha[:7],
            'latest_commit': remote_sha[:7] if remote_sha else '',
            'full_current_commit': local_sha,
            'full_latest_commit': remote_sha,
            'commit_message': remote_info['commit_message'],
            'commit_date': remote_info['commit_date'],
            'history': history
        })
    except Exception as e:
        return jsonify({'error': f'Fout bij controleren van updates: {str(e)}'}), 500

@app.route('/admin/update/apply', methods=['POST'])
@require_admin
def admin_apply_update():
    """Download en pas de nieuwste update van GitHub main branch toe."""
    try:
        try:
            result = subprocess.run(
                ['git', 'pull', 'origin', 'main'],
                capture_output=True,
                text=True,
                timeout=60
            )
        except FileNotFoundError:
            return jsonify({
                'error': 'Git is niet geïnstalleerd op de server of container.'
            }), 500

        if result.returncode != 0:
            return jsonify({
                'error': f'Git pull mislukt: {result.stderr or result.stdout}'
            }), 500

        # Installeer of update Python dependencies in requirements.txt
        try:
            pip_res = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                capture_output=True,
                text=True,
                timeout=120
            )
            if pip_res.returncode != 0:
                print(f"Waarschuwing bij pip install: {pip_res.stderr or pip_res.stdout}")
        except Exception as e:
            print(f"Fout bij installeren van dependencies: {e}")

        run_migrations()

        # Controleer de optionele vlag ?sync_to_host=true (via query arg of JSON body)
        sync_to_host_arg = request.args.get('sync_to_host', '').lower()
        req_data = request.get_json(silent=True) or {}
        sync_to_host_body = str(req_data.get('sync_to_host', '')).lower()
        sync_to_host = (sync_to_host_arg in ['true', '1']) or (sync_to_host_body in ['true', '1'])

        synced_to_host = False
        if sync_to_host:
            synced_to_host = sync_files_to_host()

        def restart_server():
            time.sleep(1)
            os._exit(0)

        threading.Thread(target=restart_server, daemon=True).start()

        return jsonify({
            'success': True,
            'message': 'Update succesvol toegepast! Server herstart nu...',
            'synced_to_host': synced_to_host,
            'output': result.stdout
        })
    except Exception as e:
        return jsonify({'error': f'Fout bij toepassen van update: {str(e)}'}), 500

@app.route('/admin/update/rollback', methods=['POST'])
@require_admin
def admin_rollback_update():
    """Rol de applicatie terug naar een opgegeven git commit SHA of naar de vorige versie."""
    try:
        req_data = request.get_json(silent=True) or {}
        target_commit = sanitize_str(req_data.get('commit', '')) or request.args.get('commit', '').strip()

        if not target_commit:
            for ref in ['ORIG_HEAD', 'HEAD~1']:
                res = subprocess.run(['git', 'rev-parse', ref], capture_output=True, text=True)
                if res.returncode == 0 and res.stdout.strip():
                    target_commit = res.stdout.strip()
                    break

        if not target_commit:
            return jsonify({'error': 'Geen geldige commit gevonden om naar terug te rollen.'}), 400

        # Valideer commit SHA via git rev-parse
        valid_res = subprocess.run(['git', 'rev-parse', '--verify', f'{target_commit}^{{commit}}'], capture_output=True, text=True)
        if valid_res.returncode != 0:
            return jsonify({'error': f'Ongeldige commit SHA: {target_commit}'}), 400

        full_commit_sha = valid_res.stdout.strip()

        try:
            result = subprocess.run(
                ['git', 'reset', '--hard', full_commit_sha],
                capture_output=True,
                text=True,
                timeout=60
            )
        except FileNotFoundError:
            return jsonify({
                'error': 'Git is niet geïnstalleerd op de server of container.'
            }), 500

        if result.returncode != 0:
            return jsonify({
                'error': f'Git reset mislukt: {result.stderr or result.stdout}'
            }), 500

        # Installeer of update Python dependencies in requirements.txt
        try:
            pip_res = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                capture_output=True,
                text=True,
                timeout=120
            )
            if pip_res.returncode != 0:
                print(f"Waarschuwing bij pip install tijdens rollback: {pip_res.stderr or pip_res.stdout}")
        except Exception as e:
            print(f"Fout bij installeren van dependencies tijdens rollback: {e}")

        run_migrations()

        sync_to_host_arg = request.args.get('sync_to_host', '').lower()
        sync_to_host_body = str(req_data.get('sync_to_host', '')).lower()
        sync_to_host = (sync_to_host_arg in ['true', '1']) or (sync_to_host_body in ['true', '1'])

        synced_to_host = False
        if sync_to_host:
            synced_to_host = sync_files_to_host()

        def restart_server():
            time.sleep(1)
            os._exit(0)

        threading.Thread(target=restart_server, daemon=True).start()

        return jsonify({
            'success': True,
            'message': f'Succesvol teruggerold naar commit {full_commit_sha[:7]}! Server herstart nu...',
            'synced_to_host': synced_to_host,
            'output': result.stdout
        })
    except Exception as e:
        return jsonify({'error': f'Fout bij terugrollen van update: {str(e)}'}), 500

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
@limiter.limit("10 per minute")
def admin_login():
    """Admin login"""
    data = request.get_json() or {}
    username = sanitize_str(data.get('username', ''))
    raw_password = data.get('password', '')
    password = raw_password if isinstance(raw_password, str) else ''

    if not username or not password:
        return jsonify({'error': 'Invalid credentials'}), 401

    users = load_users()
    user = next((u for u in users if u['username'] == username), None)

    if user and user.get('role') in ['admin', 'co-admin']:
        is_valid, needs_rehash = verify_password(user.get('password', ''), password)
        if is_valid:
            if needs_rehash:
                new_hash = hash_password(password)
                db.users.update_one({"username": username}, {"$set": {"password": new_hash}})
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

        update_data = {
            "title": new_title,
            "author": new_author,
        }
        if new_category is not None:
            update_data["category"] = new_category

        result = db.plugins.update_many(
            {"url": url},
            {"$set": update_data},
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Plugin niet gevonden'}), 404

        return jsonify({'success': True})

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

@app.route('/api/plugins/clear', methods=['POST'])
@require_login
def clear_plugins():
    """Verwijder alle plugins van de ingelogde gebruiker (of alle plugins indien admin/co-admin en `all=True`)."""
    try:
        username = session['user']
        user = get_current_user()
        req_data = request.get_json(silent=True) or {}
        delete_all = req_data.get('all', False) and user.get('role') in ['admin', 'co-admin']

        if delete_all:
            result = db.plugins.delete_many({})
        else:
            result = db.plugins.delete_many({"owner": username})

        return jsonify({'success': True, 'deleted_count': result.deleted_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_plugin', methods=['POST'])
@require_login
def delete_plugin():
    try:
        data = request.get_json()
        url = data.get('url')
        category = data.get('category')
        username = session['user']

        if not url:
            return jsonify({'error': 'Geen URL opgegeven'}), 400

        if category:
            if remove_user_plugin_category(username, url, category):
                return jsonify({'success': True, 'message': 'Categorie succesvol verwijderd'})
        else:
            if delete_user_plugin(username, url):
                return jsonify({'success': True, 'message': 'Plugin succesvol verwijderd'})

        return jsonify({'error': 'Plugin niet gevonden of fout bij verwijderen'}), 404

    except Exception as e:
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
