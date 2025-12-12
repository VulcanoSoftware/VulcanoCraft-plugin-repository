import argparse
import requests
import sys
import os
from urllib.parse import urlparse, urlunparse

# Voeg de bovenliggende map toe aan het pad om utils te kunnen importeren
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.utils import detect_platform

def remove_query_params(url):
    """Removes query parameters from a URL."""
    if url:
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
    return None

# -------- MODRINTH --------
def get_modrinth_icon(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return remove_query_params(data.get("icon_url"))
    except Exception:
        return None

# -------- SPIGOT --------
def get_spigot_icon(resource_id):
    try:
        api_url = f"https://api.spiget.org/v2/resources/{resource_id}"
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        icon_url = data.get('icon', {}).get('url')
        if icon_url:
            full_url = f"https://www.spigotmc.org/{icon_url}" if not icon_url.startswith('http') else icon_url
            return remove_query_params(full_url)
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
        return remove_query_params(data.get("avatarUrl"))
    except Exception:
        return None

# -------- CURSEFORGE --------
def get_curseforge_icon(slug):
    try:
        api_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&slug={slug}"
        headers = {
            'Accept': 'application/json',
            'x-api-key': os.environ.get('CURSEFORGE_API_KEY', '')
        }
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get('data'):
            logo = data['data'][0].get('logo')
            if logo:
                return remove_query_params(logo.get('thumbnailUrl') or logo.get('url'))
        return None
    except Exception:
        return None

# -------- GITHUB --------
def get_github_icon(owner_repo):
    try:
        owner = owner_repo.split('/')[0]
        url = f"https://api.github.com/users/{owner}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return remove_query_params(data.get("avatar_url"))
    except Exception:
        return None

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Extract plugin icon URL from various platform URLs")
    parser.add_argument("url", help="Plugin URL")
    args = parser.parse_args()

    platform, identifier = detect_platform(args.url)

    icon_url = ""
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
        print("Unsupported URL", file=sys.stderr)
        sys.exit(1)

    if icon_url:
        print(icon_url)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
