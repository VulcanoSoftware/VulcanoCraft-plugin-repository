import json
import os
import subprocess
import sys
from database import get_plugins_collection

def run_script(script_name, url):
    """Voert een Python script uit uit de fetchers map met de gegeven URL en retourneert de output"""
    # Gebruik de Python executable van de huidige omgeving
    python_executable = sys.executable
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

    # Maak het plugin object aan
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

def save_to_database(plugin):
    """Slaat een plugin op in de MongoDB database."""
    plugins_collection = get_plugins_collection()

    # Zoek de bestaande plugin op om 'owner' en 'category' te behouden
    existing_plugin = plugins_collection.find_one({'url': plugin['url']})

    # Velden die behouden moeten blijven als ze bestaan
    preserved_fields = {}
    if existing_plugin:
        if 'owner' in existing_plugin:
            preserved_fields['owner'] = existing_plugin['owner']
        if 'category' in existing_plugin:
            preserved_fields['category'] = existing_plugin['category']

    # Update het meegegeven plugin-object met de bewaarde velden
    plugin.update(preserved_fields)

    # Voer een 'upsert' uit: update de plugin als hij bestaat, voeg hem anders toe
    plugins_collection.update_one(
        {'url': plugin['url']},
        {'$set': plugin},
        upsert=True
    )
    
    print(f"Plugin {plugin['url']} is opgeslagen in de database!")

def main():
    """Hoofdfunctie voor het ophalen en optioneel opslaan van plugin data."""
    if len(sys.argv) < 2:
        print("Gebruik: python launcher.py <url> [confirm]", file=sys.stderr)
        sys.exit(1)
    
    url = sys.argv[1].strip()
    # Controleer of 'confirm' als tweede argument is meegegeven
    confirm = len(sys.argv) > 2 and sys.argv[2].lower() == 'confirm'
    
    # Haal de plugin data op
    plugin = get_plugin_data(url)
    
    # Toon de opgehaalde data als JSON
    print(json.dumps(plugin, indent=4, ensure_ascii=False))
    
    # Sla op in de database als 'confirm' is meegegeven
    if confirm:
        save_to_database(plugin)

if __name__ == "__main__":
    main()
