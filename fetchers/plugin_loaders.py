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

import re

def get_curseforge_loaders(url, api_key):
    """Haalt de loaders voor een specifiek CurseForge-project op."""
    if "bukkit-plugins" in url:
        return ["Bukkit", "Spigot", "Paper"]

    slug = extract_slug_from_url(url)
    if not slug:
        return []

    headers = {
        'x-api-key': api_key,
        'Accept': 'application/json',
    }

    try:
        # Stap 1: Zoek de mod via de slug
        params = {'gameId': 432, 'slug': slug}
        search_response = requests.get("https://api.curseforge.com/v1/mods/search", headers=headers, params=params)
        search_response.raise_for_status()
        search_data = search_response.json().get('data', [])

        if not search_data:
            return []

        mod_info = None
        for item in search_data:
            if item.get('slug') == slug:
                mod_info = item
                break

        if not mod_info:
            mod_info = search_data[0]

        mod_id = mod_info['id']

        # Stap 2: Haal bestanden op
        files_response = requests.get(f"https://api.curseforge.com/v1/mods/{mod_id}/files", headers=headers)
        files_response.raise_for_status()
        files_data = files_response.json().get('data', [])

        if not files_data:
            return []

        # Stap 3: Extraheer loaders
        loaders = set()
        for file in files_data:
            if 'gameVersions' in file:
                for version in file['gameVersions']:
                    v = version.lower()
                    if "forge" in v:
                        loaders.add("Forge")
                    elif "fabric" in v:
                        loaders.add("Fabric")
                    elif "quilt" in v:
                        loaders.add("Quilt")
                    elif "neoforge" in v:
                        loaders.add("NeoForge")

        return list(loaders) if loaders else []

    except requests.exceptions.RequestException as e:
        print(f"Fout bij het ophalen van CurseForge-projectgegevens: {e}", file=sys.stderr)
        return []

def extract_slug_from_url(url):
    """Haal de exacte slug uit de URL."""
    patterns = [
        r"mc-mods/([^/]+)",
        r"modpacks/([^/]+)",
        r"texture-packs/([^/]+)",
        r"worlds/([^/]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

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
