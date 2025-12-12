import argparse
import requests
import sys
import os

# Voeg de bovenliggende map toe aan het pad om utils te kunnen importeren
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
def get_spigot_title(resource_id):
    try:
        api_url = f"https://api.spiget.org/v2/resources/{resource_id}"
        response = requests.get(api_url)
        response.raise_for_status()
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
    try:
        api_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&slug={slug}"
        api_key = os.environ.get('CURSEFORGE_API_KEY', '')
        if not api_key:
            print("Fout: CURSEFORGE_API_KEY is niet ingesteld.", file=sys.stderr)
            return None

        headers = {
            'Accept': 'application/json',
            'x-api-key': api_key
        }
        
        response = requests.get(api_url, headers=headers)

        if response.status_code != 200:
            print(f"CurseForge API-fout (status {response.status_code}): {response.text}", file=sys.stderr)
            return None
        
        data = response.json()
        if data.get('data'):
            return data['data'][0].get('name')
        
        return None
    except requests.exceptions.RequestException as e:
        print(f"Fout bij het aanroepen van de CurseForge API: {e}", file=sys.stderr)
        return None

# -------- GITHUB --------
def get_github_title(owner_repo):
    try:
        url = f"https://api.github.com/repos/{owner_repo}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("name")
    except Exception:
        return None

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Extract plugin title from various platform URLs")
    parser.add_argument("url", help="Plugin URL")
    args = parser.parse_args()

    platform, identifier = detect_platform(args.url)

    title = ""
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
        print(f"Unsupported URL: {args.url}", file=sys.stderr)
        sys.exit(1)

    if title:
        print(title)
    else:
        print(f"Kon geen titel vinden voor {args.url}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
