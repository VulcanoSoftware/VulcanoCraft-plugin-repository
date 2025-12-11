import argparse
import os
import re
import requests
import sys
from urllib.parse import urlparse, urlunparse

# Voeg de bovenliggende map toe aan het systeempad om utils te kunnen importeren
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fetchers.utils import detect_platform

# -------- MODRINTH --------
def get_modrinth_icon(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        icon_url = data.get("icon_url")
        if icon_url:
            parsed = urlparse(icon_url)
            return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        return None
    except Exception:
        return None

# -------- SPIGOT --------
def get_spigot_icon(url):
    try:
        match = re.search(r'/resources/[^/]+\.(\d+)/?', url)
        if not match:
            return None
        
        resource_id = match.group(1)
        api_url = f"https://api.spiget.org/v2/resources/{resource_id}"
        
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        icon = data.get('icon')
        if icon and 'url' in icon:
            icon_url = f"https://www.spigotmc.org/{icon['url']}"
            return icon_url.split('?')[0]
        return None
    except Exception:
        return None

# -------- HANGAR --------
def get_hangar_icon(combined_slug):
    try:
        url = f"https://hangar.papermc.io/api/v1/projects/{combined_slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        avatar_url = data.get("avatarUrl")
        if avatar_url:
            parsed = urlparse(avatar_url)
            return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        return None
    except Exception:
        return None

# -------- CURSEFORGE --------
def get_curseforge_icon(slug):
    """Haalt de icoon URL van een CurseForge/Bukkit plugin op."""
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
                    logo = mod.get('logo')
                    if logo:
                        # Geef de voorkeur aan thumbnailUrl voor een kleiner formaat
                        icon_url = logo.get('thumbnailUrl') or logo.get('url')
                        return icon_url.split('?')[0] if icon_url else None
        return None
    except Exception:
        return None

# -------- GITHUB --------
def get_github_icon(repo_identifier):
    """Haalt de avatar van de eigenaar van een GitHub repository op."""
    try:
        api_url = f"https://api.github.com/repos/{repo_identifier}"
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        owner_data = data.get('owner')
        if owner_data and 'avatar_url' in owner_data:
            avatar_url = owner_data['avatar_url']
            return avatar_url.split('?')[0]
        return None
    except Exception:
        return None

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Extraheer pluginicoon URL van ondersteunde platformen.")
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

    icon_url = None
    if platform == "modrinth":
        icon_url = get_modrinth_icon(identifier)
    elif platform == "spigot":
        icon_url = get_spigot_icon(identifier)
    elif platform == "hangar":
        icon_url = get_hangar_icon(identifier)
    elif platform == "curseforge":
        icon_url = get_curseforge_icon(identifier)
    elif platform == "github":
        icon_url = get_github_icon(identifier)
    else:
        print(f"Platform '{platform}' wordt nog niet ondersteund.", file=sys.stderr)
        sys.exit(1)

    if icon_url is None:
        print("")
        sys.exit(0)
    else:
        print(icon_url)

if __name__ == "__main__":
    main()
