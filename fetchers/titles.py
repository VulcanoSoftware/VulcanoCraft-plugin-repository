import argparse
import re
import requests
import sys
from urllib.parse import urlparse

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
def get_curseforge_title(url):
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
            return data['data'][0].get('name')
        
        return None
    except Exception:
        return None

# -------- GITHUB --------
def get_github_title(repo):
    try:
        url = f"https://api.github.com/repos/{repo}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("name")
    except Exception:
        return None

from utils import detect_platform

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Extract plugin title from Modrinth, SpigotMC, or Hangar URLs")
    parser.add_argument("url", nargs="?", help="Plugin URL from Modrinth, SpigotMC, or Hangar")
    args = parser.parse_args()

    if not args.url:
        args.url = input("Enter a plugin URL: ").strip()

    platform, identifier = detect_platform(args.url)
    if not platform:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

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
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if title is None:
        print("", file=sys.stderr)
        sys.exit(1)
    else:
        print(title)

if __name__ == "__main__":
    main()