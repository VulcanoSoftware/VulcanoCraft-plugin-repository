import argparse
import os
import re
import requests
import sys
from urllib.parse import urlparse

# Voeg de bovenliggende map toe aan het systeempad om utils te kunnen importeren
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fetchers.utils import detect_platform

# -------- MODRINTH --------
def get_modrinth_versions(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}/version"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        versions = set()
        for version_data in data:
            versions.update(version_data.get("game_versions", []))
        return sorted(list(versions))
    except Exception:
        return []

# -------- SPIGOT --------
def get_spigot_versions(url):
    try:
        match = re.search(r'/resources/[^/]+\.(\d+)/?', url)
        if not match:
            return []
        
        resource_id = match.group(1)
        api_url = f"https://api.spiget.org/v2/resources/{resource_id}"
        
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        return sorted(data.get('testedVersions', []))
    except Exception:
        return []

# -------- HANGAR --------
def get_hangar_versions(combined_slug):
    try:
        url = f"https://hangar.papermc.io/api/v1/projects/{combined_slug}/versions"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        versions = set()
        for version_data in data.get("result", []):
            for deps in version_data.get("platformDependencies", {}).values():
                versions.update(deps)
        return sorted(list(versions))
    except Exception:
        return []

# -------- CURSEFORGE --------
def get_curseforge_versions(slug):
    """Haalt de ondersteunde gameversies voor een CurseForge/Bukkit plugin op."""
    try:
        api_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&slug={slug}"
        headers = {
            'Accept': 'application/json',
            'x-api-key': os.environ.get('CURSEFORGE_API_KEY', '$2a$10$bL4bIL5pUWqfcO7KQtnMReakwtfHbNKh6v1uTpKlzhwoueEJQnPnm')
        }
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not data.get('data'):
            return []

        versions = set()
        for mod in data['data']:
            if mod.get('slug') == slug:
                # 'latestFilesIndexes' bevat een lijst van bestanden met hun gameversies.
                for file_index in mod.get('latestFilesIndexes', []):
                    game_version = file_index.get('gameVersion')
                    if game_version:
                        versions.add(game_version)
                # We hebben de juiste mod gevonden en de versies verzameld.
                break
        
        return sorted(list(versions))
    except Exception:
        return []

# -------- GITHUB --------
def get_github_versions(repo_identifier):
    """Haalt de 'tags' (die vaak als versies dienen) van een GitHub repository op."""
    try:
        api_url = f"https://api.github.com/repos/{repo_identifier}/tags"
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        # We halen de 'name' van elke tag op, bv. "v1.2.3" of "1.2.3"
        # We filteren eventuele niet-numerieke tags eruit.
        versions = [tag['name'].lstrip('v') for tag in data if re.match(r'v?\d', tag.get('name', ''))]
        return sorted(versions)
    except Exception:
        return []

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Extraheer ondersteunde versies van een plugin.")
    parser.add_argument("url", nargs="?", help="Plugin URL")
    args = parser.parse_args()

    if not args.url:
        if sys.stdin.isatty():
            args.url = input("Voer een plugin URL in: ").strip()
        else:
            args.url = sys.stdin.read().strip()

    platform, identifier = detect_platform(args.url)

    if not platform:
        print("Ongeldige of niet-ondersteunde URL", file=sys.stderr)
        sys.exit(1)

    versions = []
    if platform == "modrinth":
        versions = get_modrinth_versions(identifier)
    elif platform == "spigot":
        versions = get_spigot_versions(identifier)
    elif platform == "hangar":
        versions = get_hangar_versions(identifier)
    elif platform == "curseforge":
        versions = get_curseforge_versions(identifier)
    elif platform == "github":
        versions = get_github_versions(identifier)
    else:
        print(f"Platform '{platform}' wordt nog niet ondersteund.", file=sys.stderr)
        sys.exit(1)

    if versions:
        print(" ".join(versions))
    else:
        print("")

if __name__ == "__main__":
    main()
