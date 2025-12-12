import json
import os
import subprocess
import sys
from pymongo import MongoClient

# -------- DATABASE CONNECTION --------
def get_db():
    """Maakt verbinding met de MongoDB database."""
    try:
        client = MongoClient(os.environ.get("MONGO_URI"))
        db = client[os.environ.get("MONGO_DB_NAME")]
        return db
    except Exception as e:
        print(f"Kon geen verbinding maken met de database: {e}", file=sys.stderr)
        sys.exit(1)

# -------- SCRIPT EXECUTION --------
def run_script(script_name, url, api_key=None):
    """Voert een Python script uit uit de fetchers map en retourneert de output."""
    python_executable = sys.executable
    script_path = os.path.join(os.path.dirname(__file__), 'fetchers', f'{script_name}.py')

    env = os.environ.copy()
    if api_key:
        env['CURSEFORGE_API_KEY'] = api_key

    try:
        result = subprocess.run(
            [python_executable, script_path, url],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Fout bij uitvoeren {script_path}: {e.stderr}", file=sys.stderr)
        return ""

# -------- PLUGIN DATA HANDLING --------
def get_plugin_data(url):
    """Haalt alle plugin data op voor een gegeven URL."""
    print(f"Ophalen van data voor: {url}...")
    
    # Haal API key op uit environment
    api_key = os.environ.get("CURSEFORGE_API_KEY")

    # Scripts parallel uitvoeren zou sneller zijn, maar sequentieel voor eenvoud
    title = run_script('titles', url, api_key)
    description = run_script('description', url, api_key)
    author = run_script('author', url, api_key)
    icon = run_script('icon', url, api_key)
    versions_str = run_script('versions', url, api_key)
    loaders_json = run_script('loaders', url, api_key)
    
    # Converteer output naar juiste formaten
    versions = versions_str.split(' ') if versions_str else []
    try:
        loaders = json.loads(loaders_json)
    except json.JSONDecodeError:
        loaders = []

    plugin = {
        "url": url,
        "title": title,
        "description": description,
        "author": author,
        "icon": icon,
        "versions": versions,
        "loaders": loaders
    }
    
    print("Data succesvol opgehaald.")
    return plugin

def save_to_db(db, plugin):
    """Slaat een plugin op in de database."""
    plugins_collection = db.plugins

    # Zoek bestaande plugin om 'owner' veld te behouden
    existing_plugin = plugins_collection.find_one({"url": plugin['url']})
    if existing_plugin and 'owner' in existing_plugin:
        plugin['owner'] = existing_plugin['owner']
    
    # Gebruik update_one met upsert=True om de plugin toe te voegen of bij te werken
    plugins_collection.update_one(
        {"url": plugin['url']},
        {"$set": plugin},
        upsert=True
    )
    print(f"Plugin {plugin['url']} is opgeslagen in de database!")

# -------- MAIN --------
def main():
    if len(sys.argv) < 2:
        print("Gebruik: python launcher.py <url> [confirm]", file=sys.stderr)
        sys.exit(1)
    
    url = sys.argv[1].strip()
    confirm = len(sys.argv) > 2 and sys.argv[2].lower() == 'confirm'
    
    plugin = get_plugin_data(url)
    
    print("\n--- Opgehaalde Plugin Data ---")
    print(json.dumps(plugin, indent=4, ensure_ascii=False))
    print("----------------------------\n")

    if confirm:
        db = get_db()
        save_to_db(db, plugin)
    else:
        print("Gebruik 'confirm' als derde argument om de data op te slaan in de database.")

if __name__ == "__main__":
    main()