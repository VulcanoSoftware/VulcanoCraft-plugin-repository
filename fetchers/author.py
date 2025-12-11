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
def get_modrinth_author(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        team_id = data.get("team")
        if not team_id:
            return None
            
        team_url = f"https://api.modrinth.com/v2/team/{team_id}/members"
        team_response = requests.get(team_url)
        team_response.raise_for_status()
        team_data = team_response.json()
        
        authors = [member['user']['username'] for member in team_data if 'user' in member and member['user'].get('username')]
        return " ".join(authors) if authors else None
        
    except Exception:
        return None

# -------- SPIGOT --------
def get_spigot_author(url):
    try:
        match = re.search(r'/resources/[^/]+\.(\d+)/?', url)
        if not match:
            return None
        
        resource_id = match.group(1)
        api_url = f"https://api.spiget.org/v2/resources/{resource_id}/author"
        
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        return data.get('name')
    except Exception:
        return None

# -------- HANGAR --------
def get_hangar_author(combined_slug):
    try:
        return combined_slug.split('/')[0]
    except Exception:
        return None

# -------- CURSEFORGE --------
def get_curseforge_author(slug):
    """Haalt de auteur van een CurseForge/Bukkit plugin op."""
    try:
        api_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&slug={slug}"
        headers = {
            'Accept': 'application/json',
            'x-api-key': os.environ.get('CURSEFORGE_API_KEY', '$2a$10$bL4bIL5pUWqfcO7KQtnMReakwtfHbNKh6v1uTpKlzhwoueEJQnPnm')
        }
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get('data'):
            for mod in data['data']:
                if mod.get('slug') == slug:
                    authors = mod.get('authors', [])
                    if authors:
                        return authors[0].get('name')
        return None
    except Exception:
        return None

# -------- GITHUB --------
def get_github_author(repo_identifier):
    """Haalt de eigenaar van een GitHub repository op."""
    try:
        api_url = f"https://api.github.com/repos/{repo_identifier}"
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        # 'owner' is een object, we willen de 'login' naam.
        return data.get('owner', {}).get('login')
    except Exception:
        return None

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Extraheer pluginauteur van ondersteunde platformen.")
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

    author = None
    if platform == "modrinth":
        author = get_modrinth_author(identifier)
    elif platform == "spigot":
        author = get_spigot_author(identifier)
    elif platform == "hangar":
        author = get_hangar_author(identifier)
    elif platform == "curseforge":
        author = get_curseforge_author(identifier)
    elif platform == "github":
        author = get_github_author(identifier)
    else:
        print(f"Platform '{platform}' wordt nog niet ondersteund.", file=sys.stderr)
        sys.exit(1)

    if author is None:
        print("")
        sys.exit(0)
    else:
        print(author)

if __name__ == "__main__":
    main()
