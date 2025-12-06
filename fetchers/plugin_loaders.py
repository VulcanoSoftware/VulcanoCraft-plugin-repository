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

    headers = {'x-api-key': api_key}
    slug = url.rstrip('/').split('/')[-1]

    try:
        params = {'gameId': 432, 'slug': slug, 'classId': 6} # classId 6 is for Mods
        search_response = requests.get("https://api.curseforge.com/v1/mods/search", headers=headers, params=params)
        search_response.raise_for_status()
        search_data = search_response.json().get('data', [])

        if not search_data:
            return []

        mod_id = search_data[0]['id']
        mod_response = requests.get(f"https://api.curseforge.com/v1/mods/{mod_id}", headers=headers)
        mod_response.raise_for_status()
        mod_data = mod_response.json().get('data', {})

        loaders = set()
        if 'latestFilesIndexes' in mod_data:
            for file_index in mod_data['latestFilesIndexes']:
                # Fabric/Quilt/Forge
                if 'modLoader' in file_index and file_index['modLoader'] is not None:
                    modloader_map = {0: "Any", 1: "Forge", 2: "Cauldron", 3: "LiteLoader", 4: "Fabric", 5: "Quilt", 6: "NeoForge"}
                    if file_index['modLoader'] in modloader_map:
                        loaders.add(modloader_map[file_index['modLoader']])

        # Fallback for mods that don't have the modLoader field populated
        if not loaders and 'categories' in mod_data:
            for category in mod_data['categories']:
                if category['slug'] == 'fabric':
                    loaders.add('Fabric')
                elif category['slug'] == 'forge':
                    loaders.add('Forge')
                elif category['slug'] == 'quilt':
                    loaders.add('Quilt')


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
