import argparse
import requests
import sys
import os

# Voeg de bovenliggende map toe aan het pad om utils te kunnen importeren
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
def get_spigot_author(resource_id):
    try:
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
            authors = data['data'][0].get('authors', [])
            if authors:
                return authors[0].get('name')
        
        return None
    except Exception:
        return None

# -------- GITHUB --------
def get_github_author(owner_repo):
    try:
        return owner_repo.split('/')[0]
    except Exception:
        return None

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Extract plugin author from various platform URLs")
    parser.add_argument("url", help="Plugin URL")
    args = parser.parse_args()

    platform, identifier = detect_platform(args.url)

    author = ""
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
        print("Unsupported URL", file=sys.stderr)
        sys.exit(1)

    if author:
        print(author)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
