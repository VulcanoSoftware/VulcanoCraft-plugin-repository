import argparse
import re
import requests
import sys
from urllib.parse import urlparse, urlunparse

# -------- MODRINTH --------
def get_modrinth_icon(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        icon_url = data.get("icon_url")
        if icon_url:
            # Verwijder query parameters
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
        if response.status_code != 200:
            return None
        
        data = response.json()
        icon = data.get('icon')
        if icon and 'url' in icon:
            icon_url = icon['url']
            if not icon_url.startswith('http'):
                icon_url = f"https://www.spigotmc.org/{icon_url}"
            if '?' in icon_url:
                icon_url = icon_url.split('?')[0]
            return icon_url
        
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
        
        # Gebruik het avatarUrl veld en verwijder query parameters
        avatar_url = data.get("avatarUrl")
        if avatar_url:
            parsed = urlparse(avatar_url)
            return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        return None
        
    except Exception:
        return None

# -------- CURSEFORGE --------
def get_curseforge_icon(url):
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if "dev.bukkit.org" in url:
            project_slug = path_parts[1]
            class_id = 5
        else:
            category = path_parts[1]
            project_slug = path_parts[2]
            if category == 'bukkit-plugins':
                class_id = 5
            elif category == 'mc-mods':
                class_id = 6
            elif category == 'modpacks':
                class_id = 4471
            else:
                return None

        api_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&slug={project_slug}&classId={class_id}"
        
        headers = {
            'Accept': 'application/json',
            'x-api-key': '$2a$10$bL4bIL5pUWqfcO7KQtnMReakwtfHbNKh6v1uTpKlzhwoueEJQnPnm'
        }
        
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            return None
        
        data = response.json()
        if data.get('data'):
            logo = data['data'][0].get('logo')
            if logo:
                icon_url = logo.get('thumbnailUrl') or logo.get('url')
                if icon_url and '?' in icon_url:
                    icon_url = icon_url.split('?')[0]
                return icon_url
        
        return None
    except Exception:
        return None

# -------- GITHUB --------
def get_github_icon(repo):
    try:
        url = f"https://api.github.com/repos/{repo}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        owner_data = data.get("owner", {})
        avatar_url = owner_data.get("avatar_url")
        if avatar_url and '?' in avatar_url:
            avatar_url = avatar_url.split('?')[0]
        return avatar_url
    except Exception:
        return None

from utils import detect_platform

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Extract plugin icon URL from Modrinth, SpigotMC, or Hangar URLs")
    parser.add_argument("url", nargs="?", help="Plugin URL from Modrinth, SpigotMC, or Hangar")
    args = parser.parse_args()

    if not args.url:
        args.url = input("Enter a plugin URL: ").strip()

    platform, identifier = detect_platform(args.url)
    if not platform:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

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
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if icon_url is None:
        print("", file=sys.stderr)
        sys.exit(1)
    else:
        print(icon_url)

if __name__ == "__main__":
    main()