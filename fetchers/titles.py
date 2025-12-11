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
def get_modrinth_title(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("title")
    except Exception:
        return None

# -------- SPIGOT --------
def get_spigot_title(url):
    try:
        match = re.search(r'/resources/[^/]+\.(\d+)/?', url)
        if not match:
            return None
        
        resource_id = match.group(1)
        api_url = f"https://api.spiget.org/v2/resources/{resource_id}"
        
        response = requests.get(api_url)
        if response.status_code != 200:
            return None
        
        data = response.json()
        return data.get('name')
    except Exception:
        return None

# -------- HANGAR --------
def get_hangar_title(combined_slug):
    try:
        url = f"https://hangar.papermc.io/api/v1/projects/{combined_slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("name")
    except Exception:
        return None

# -------- CURSEFORGE --------
def get_curseforge_title(slug):
    """Haalt de titel van een CurseForge/Bukkit plugin op via de slug."""
    try:
        # We zoeken zonder classId om het algemeen te houden voor alle project types.
        api_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&slug={slug}"
        
        headers = {
            'Accept': 'application/json',
            'x-api-key': os.environ.get('CURSEFORGE_API_KEY', '$2a$10$bL4bIL5pUWqfcO7KQtnMReakwtfHbNKh6v1uTpKlzhwoueEJQnPnm')
        }
        
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if data.get('data'):
            # De zoekopdracht kan meerdere resultaten geven, we nemen de eerste die exact overeenkomt.
            for mod in data['data']:
                if mod.get('slug') == slug:
                    return mod.get('name')
        return None
    except Exception:
        return None

# -------- GITHUB --------
def get_github_title(repo_identifier):
    """Haalt de titel (repositorynaam) van een GitHub repository op."""
    try:
        api_url = f"https://api.github.com/repos/{repo_identifier}"
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        # Gebruik 'name' voor de pure repositorynaam, 'full_name' bevat ook de eigenaar.
        return data.get("name")
    except Exception:
        return None

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Extraheer plugintitel van ondersteunde platformen.")
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

    title = None
    if platform == "modrinth":
        title = get_modrinth_title(identifier)
    elif platform == "spigot":
        title = get_spigot_title(identifier)
    elif platform == "hangar":
        title = get_hangar_title(identifier)
    elif platform == "curseforge":
        title = get_curseforge_title(identifier)
    elif platform == "github":
        title = get_github_title(identifier)
    else:
        print(f"Platform '{platform}' wordt nog niet ondersteund.", file=sys.stderr)
        sys.exit(1)

    if title is None:
        # Een lege output is prima als er geen titel is, maar we vermijden een fout.
        print("")
        sys.exit(0)
    else:
        print(title)

if __name__ == "__main__":
    main()
