import argparse
import requests
import sys
import os
import re

# Voeg de bovenliggende map toe aan het pad om utils te kunnen importeren
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.utils import detect_platform

# -------- MODRINTH --------
def get_modrinth_versions(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}/version"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        versions = set()
        for version_info in data:
            versions.update(version_info.get("game_versions", []))

        return sorted(list(versions))
    except Exception:
        return []

# -------- SPIGOT --------
def get_spigot_versions(resource_id):
    try:
        api_url = f"https://api.spiget.org/v2/resources/{resource_id}"
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        return data.get('testedVersions', [])
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
        if 'result' in data:
            for version_info in data['result']:
                for deps in version_info.get('platformDependencies', {}).values():
                    versions.update(deps)
        return sorted(list(versions))
    except Exception:
        return []

# -------- CURSEFORGE --------
def get_curseforge_versions(slug):
    try:
        api_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&slug={slug}"
        headers = {
            'Accept': 'application/json',
            'x-api-key': os.environ.get('CURSEFORGE_API_KEY', '')
        }
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not data.get('data'):
            return []

        versions = set()
        mod_info = data['data'][0]
        for file_index in mod_info.get('latestFilesIndexes', []):
            game_version = file_index.get('gameVersion')
            if game_version and re.match(r'^\d+\.\d+(\.\d+)?$', game_version):
                 versions.add(game_version)

        return sorted(list(versions))
    except Exception:
        return []

# -------- GITHUB --------
def get_github_versions(owner_repo):
    # Kan niet betrouwbaar worden bepaald vanaf GitHub
    return []

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Extract plugin versions from various platform URLs")
    parser.add_argument("url", help="Plugin URL")
    args = parser.parse_args()

    platform, identifier = detect_platform(args.url)

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
        print("Unsupported URL", file=sys.stderr)
        sys.exit(1)

    if versions:
        print(" ".join(versions))
    else:
        print("")

if __name__ == "__main__":
    main()
