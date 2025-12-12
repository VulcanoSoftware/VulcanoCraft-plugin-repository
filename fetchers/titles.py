import argparse
import re
import requests
import sys
from urllib.parse import urlparse
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

import os

# -------- CURSEFORGE --------
def get_curseforge_title(url):
    try:
        api_key = os.environ.get('CURSEFORGE_API_KEY')
        if not api_key:
            print("CURSEFORGE_API_KEY not set", file=sys.stderr)
            return None

        # Extract slug from URL
        match = re.search(r'/(projects|bukkit-plugins)/([^/]+)', url)
        if not match:
            # Fallback for URLs like /minecraft/mc-mods/...
            match = re.search(r'/(mc-mods)/([^/]+)', url)
        
        if not match:
            return None
        
        project_slug = match.group(2)

        api_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&slug={project_slug}"
        
        headers = {
            'Accept': 'application/json',
            'x-api-key': api_key
        }
        
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if data.get('data'):
            return data['data'][0].get('name')
        
        return None
    except Exception as e:
        print(f"Error fetching CurseForge title: {e}", file=sys.stderr)
        return None

# -------- GITHUB --------
def get_github_title(repo_slug):
    try:
        url = f"https://api.github.com/repos/{repo_slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("name")
    except Exception:
        return None

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
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if title is None:
        print("", file=sys.stderr)
        sys.exit(1)
    else:
        print(title)

if __name__ == "__main__":
    main()