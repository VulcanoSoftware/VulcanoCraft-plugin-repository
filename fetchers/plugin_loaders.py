import sys
import requests
import json
import os

def get_modrinth_loaders(project_id):
    """Haalt de loaders voor een specifiek Modrinth-project op."""
    try:
        response = requests.get(f"https://api.modrinth.com/v2/project/{project_id}")
        response.raise_for_status()
        project_data = response.json()
        return project_data.get("loaders", [])
    except requests.exceptions.RequestException as e:
        print(f"Fout bij het ophalen van Modrinth-projectgegevens: {e}", file=sys.stderr)
        return []

def get_spigotmc_loaders(resource_id):
    """Haalt de loaders voor een specifiek SpigotMC-resource op."""
    try:
        # We still ping the API to ensure the resource exists, but the loaders are hardcoded.
        response = requests.get(f"https://api.spiget.org/v2/resources/{resource_id}")
        response.raise_for_status()
        return ["Spigot", "Paper", "Bukkit"]
    except requests.exceptions.RequestException as e:
        print(f"Fout bij het ophalen van SpigotMC-resourcegegevens: {e}", file=sys.stderr)
        return []

def get_hangar_loaders(author, slug):
    """Haalt de loaders voor een specifiek Hangar-project op."""
    try:
        response = requests.get(f"https://hangar.papermc.io/api/v1/projects/{author}/{slug}/versions")
        response.raise_for_status()
        versions_data = response.json()
        loaders = set()
        for version in versions_data.get('result', []):
            for dependency in version.get('platformDependencies', {}):
                loaders.add(dependency)
        return list(loaders)
    except requests.exceptions.RequestException as e:
        print(f"Fout bij het ophalen van Hangar-projectgegevens: {e}", file=sys.stderr)
        return []

def get_curseforge_loaders(url, api_key):
    """Haalt de loaders voor een specifiek CurseForge-project op."""
    if "bukkit-plugins" in url:
        return ["Bukkit", "Spigot", "Paper"]

    headers = {
        'x-api-key': api_key,
        'Accept': 'application/json',
    }
    slug = url.rstrip('/').split('/')[-1]

    try:
        # Stap 1: Zoek de mod via de slug (zonder classId)
        params = {'gameId': 432, 'slug': slug}
        search_response = requests.get("https://api.curseforge.com/v1/mods/search", headers=headers, params=params)
        search_response.raise_for_status()
        search_data = search_response.json().get('data', [])

        if not search_data:
            return []

        # Omdat de API soms meerdere resultaten geeft, filteren we op classId
        mod_info = None
        if "bukkit-plugins" in url:
            for item in search_data:
                if item.get('slug') == slug and item.get('classId') == 5:
                    mod_info = item
                    break
        else:
            for item in search_data:
                if item.get('slug') == slug and item.get('classId') == 6:
                    mod_info = item
                    break

        if not mod_info:
            # Fallback naar het eerste resultaat als er geen exacte match is
            if search_data:
                mod_info = search_data[0]
            else:
                return []

        mod_id = mod_info['id']
        class_id = mod_info['classId']

        # Stap 2: Controleer de classId en retourneer specifieke loaders
        # 5 = Bukkit Plugins
        if class_id == 5:
            return ["Bukkit", "Spigot", "Paper"]

        # Stap 3: Haal gedetailleerde mod-informatie op
        mod_response = requests.get(f"https://api.curseforge.com/v1/mods/{mod_id}", headers=headers)
        mod_response.raise_for_status()
        mod_data = mod_response.json().get('data', {})

        loaders = set()
        if 'latestFilesIndexes' in mod_data:
            for file_index in mod_data['latestFilesIndexes']:
                if 'modLoader' in file_index and file_index['modLoader'] is not None:
                    modloader_map = {
                        0: "Any", 1: "Forge", 2: "Cauldron", 3: "LiteLoader",
                        4: "Fabric", 5: "Quilt", 6: "NeoForge"
                    }
                    loader = modloader_map.get(file_index['modLoader'])
                    if loader:
                        loaders.add(loader)

        # Fallback: controleer de categorieën als er geen loaders zijn gevonden
        if not loaders and 'categories' in mod_data:
            for category in mod_data['categories']:
                if category['slug'] in ['fabric', 'forge', 'quilt', 'neoforge']:
                    loaders.add(category['slug'].capitalize())

        return list(loaders) if loaders else []

    except requests.exceptions.RequestException as e:
        print(f"Fout bij het ophalen van CurseForge-projectgegevens: {e}", file=sys.stderr)
        return []

def main():
    if len(sys.argv) < 2:
        print("Gebruik: python fetchers/plugin_loaders.py <url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]

    if "modrinth.com" in url:
        project_id = url.split('/')[-1]
        loaders = get_modrinth_loaders(project_id)
        print(json.dumps(loaders))
    elif "spigotmc.org" in url:
        try:
            resource_id = url.split('.')[-1].split('/')[0]
            loaders = get_spigotmc_loaders(resource_id)
            print(json.dumps(loaders))
        except IndexError:
            print(json.dumps([]))
    elif "hangar.papermc.io" in url:
        parts = url.strip('/').split('/')
        author = parts[-2]
        slug = parts[-1]
        loaders = get_hangar_loaders(author, slug)
        print(json.dumps(loaders))
    elif "curseforge.com" in url:
        api_key = os.environ.get("CURSEFORGE_API_KEY")
        if not api_key:
            print("Fout: CURSEFORGE_API_KEY omgevingsvariabele niet ingesteld.", file=sys.stderr)
            sys.exit(1)

        loaders = get_curseforge_loaders(url, api_key)
        print(json.dumps(loaders))
    else:
        print(json.dumps([]))

if __name__ == "__main__":
    main()
