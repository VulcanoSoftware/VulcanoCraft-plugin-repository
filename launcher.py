import json
import os
import subprocess
import sys
from pymongo import MongoClient

def run_script(script_name, url):
    """Voert een Python script uit uit de fetchers map met de gegeven URL en retourneert de output"""
    python_executable = ".venv/bin/python" if os.path.exists(".venv/bin/python") else sys.executable
    try:
        result = subprocess.run(
            [python_executable, f'fetchers/{script_name}.py', url],
            capture_output=True,
            text=True,
            check=True,
            env=os.environ.copy()
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Fout bij uitvoeren fetchers/{script_name}.py: {e}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        return ""

def get_plugin_data(url):
    """Haalt alle plugin data op voor een gegeven URL"""
    versions = run_script('versions', url)
    
    titles = run_script('titles', url)
    
    icon = run_script('icon', url)
    
    description = run_script('description', url)
    
    author = run_script('author', url)
    
    loaders_json = run_script('loaders', url)
    try:
        loaders = json.loads(loaders_json)
    except json.JSONDecodeError:
        loaders = []

    # Maak plugin object
    plugin = {
        "url": url,
        "title": titles,
        "description": description,
        "author": author,
        "icon": icon,
        "versions": versions,
        "loaders": loaders
    }
    
    return plugin

def save_to_file(plugin):
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db_name = os.getenv("MONGO_DB_NAME", "vulcanocraft")
    mongo_client = MongoClient(mongo_uri)
    db = mongo_client[mongo_db_name]
    plugins_collection = db.plugins
    existing_plugin = plugins_collection.find_one({"url": plugin["url"]})
    if existing_plugin and existing_plugin.get("owner") and not plugin.get("owner"):
        plugin["owner"] = existing_plugin["owner"]
    plugins_collection.update_one(
        {"url": plugin["url"], "owner": plugin.get("owner")},
        {"$set": plugin},
        upsert=True,
    )
    print(f"Plugin {plugin['url']} is opgeslagen in de database!")

def main():
    # Controleer command-line argumenten
    if len(sys.argv) < 2:
        print("Gebruik: python launcher.py <url> [confirm]")
        sys.exit(1)
    
    url = sys.argv[1].strip()
    confirm = len(sys.argv) > 2 and sys.argv[2].lower() == 'confirm'
    
    # Haal plugin data op
    plugin = get_plugin_data(url)
    
    # Toon de JSON structuur
    print(json.dumps(plugin, indent=4, ensure_ascii=False))
    
    # Als confirm is opgegeven, sla dan op
    if confirm:
        save_to_file(plugin)

if __name__ == "__main__":
    main()
