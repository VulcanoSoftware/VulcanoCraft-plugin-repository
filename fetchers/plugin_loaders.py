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

def get_curseforge_loaders(project_id):
    """Haalt de loaders voor een specifiek CurseForge-project op."""
    api_key = os.environ.get("CURSEFORGE_API_KEY")
    if not api_key:
        print("Fout: CURSEFORGE_API_KEY omgevingsvariabele niet ingesteld.", file=sys.stderr)
        return []
    try:
        headers = {'x-api-key': api_key}
        # The API doesn't seem to use the project_id directly, so we search by slug
        response = requests.get(f"https://api.curseforge.com/v1/mods/{project_id}", headers=headers)

        response.raise_for_status()
        mod_data = response.json().get('data', {})
        loaders = set()
        if 'latestFilesIndexes' in mod_data:
            for file_index in mod_data['latestFilesIndexes']:
                if 'modLoader' in file_index and file_index['modLoader'] is not None:
                    modloader_map = {0: "Any", 1: "Forge", 2: "Cauldron", 3: "LiteLoader", 4: "Fabric", 5: "Quilt", 6: "NeoForge"}
                    loaders.add(modloader_map.get(file_index['modLoader'], "Unknown"))
        if not loaders and 'latestFiles' in mod_data:
            for file in mod_data['latestFiles']:
                if 'bukkit' in file['fileName'].lower():
                    return ["Bukkit", "Spigot", "Paper"]
        return list(loaders) if loaders else ["Unknown"]
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
        headers = {'x-api-key': api_key}
        slug = url.rstrip('/').split('/')[-1]
        class_id = 5 if "bukkit-plugins" in url else None
        try:
            params = {'gameId': 432, 'slug': slug}
            if class_id:
                params['classId'] = class_id
            search_response = requests.get("https://api.curseforge.com/v1/mods/search", headers=headers, params=params)
            search_response.raise_for_status()
            search_data = search_response.json().get('data', [])
            project_id = None
            if search_data:
                if class_id:
                    for project in search_data:
                        if project.get('classId') == class_id:
                            project_id = project['id']
                            break
                if not project_id:
                    project_id = search_data[0]['id']

            if project_id:
                loaders = get_curseforge_loaders(project_id)
                print(json.dumps(loaders))
            else:
                print(json.dumps([]))
        except requests.exceptions.RequestException as e:
            print(f"Fout bij het zoeken naar CurseForge-project: {e}", file=sys.stderr)
            print(json.dumps([]))
    else:
        print(json.dumps([]))

if __name__ == "__main__":
    main()
