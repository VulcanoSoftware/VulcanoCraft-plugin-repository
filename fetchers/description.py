import argparse
import requests
import sys
import os

# Voeg de bovenliggende map toe aan het pad om utils te kunnen importeren
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.utils import detect_platform

# -------- MODRINTH --------
def get_modrinth_description(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("description")
    except Exception:
        return None

# -------- SPIGOT --------
def get_spigot_description(resource_id):
    try:
        api_url = f"https://api.spiget.org/v2/resources/{resource_id}"
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        return data.get('tag')
    except Exception:
        return None

# -------- HANGAR --------
def get_hangar_description(combined_slug):
    try:
        url = f"https://hangar.papermc.io/api/v1/projects/{combined_slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("description")
    except Exception:
        return None

# -------- CURSEFORGE --------
def get_curseforge_description(slug):
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
            return data['data'][0].get('summary')
        
        return None
    except Exception:
        return None

# -------- GITHUB --------
def get_github_description(owner_repo):
    try:
        url = f"https://api.github.com/repos/{owner_repo}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("description")
    except Exception:
        return None

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Extract plugin description from various platform URLs")
    parser.add_argument("url", help="Plugin URL")
    args = parser.parse_args()

    platform, identifier = detect_platform(args.url)

    description = ""
    if platform == "modrinth":
        description = get_modrinth_description(identifier)
    elif platform == "spigot":
        description = get_spigot_description(identifier)
    elif platform == "hangar":
        description = get_hangar_description(identifier)
    elif platform == "curseforge":
        description = get_curseforge_description(identifier)
    elif platform == "github":
        description = get_github_description(identifier)
    else:
        print("Unsupported URL", file=sys.stderr)
        sys.exit(1)

    if description:
        print(description)
    else:
        # Return a non-error empty response if description is empty or None
        print("")

if __name__ == "__main__":
    main()
