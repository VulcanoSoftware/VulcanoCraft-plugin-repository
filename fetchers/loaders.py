import argparse
import requests
import sys
import os
import json

# Voeg de bovenliggende map toe aan het pad om utils te kunnen importeren
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.utils import detect_platform

# -------- MODRINTH --------
def get_modrinth_loaders(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("loaders", [])
    except Exception:
        return []

# -------- SPIGOT --------
def get_spigot_loaders(resource_id):
    # Spigot/Bukkit plugins zijn compatibel met Paper, Spigot, Bukkit
    return ["Paper", "Spigot", "Bukkit"]

# -------- HANGAR --------
def get_hangar_loaders(combined_slug):
    try:
        # Hangar's API geeft niet altijd de juiste loaders terug.
        # PaperMC/Velocity is een bekend voorbeeld.
        if combined_slug.lower() == 'papermc/velocity':
            return ["PAPER", "VELOCITY", "WATERFALL"]

        url = f"https://hangar.papermc.io/api/v1/projects/{combined_slug}/versions"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        loaders = set()
        if 'result' in data:
            for version_info in data['result']:
                for platform in version_info.get('platformDependencies', {}):
                    loaders.add(platform.upper())
        return list(loaders) if loaders else []
    except Exception:
        return []

# -------- CURSEFORGE --------
def get_curseforge_loaders(slug):
    try:
        api_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&slug={slug}"
        headers = {
            'Accept': 'application/json',
            'x-api-key': os.environ.get('CURSEFORGE_API_KEY', '')
        }
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not data.get('data'):
            return []

        mod_id = data['data'][0]['id']

        # Voor Bukkit-plugins, retourneer een standaardlijst
        if any(cat.get('slug') == 'bukkit-plugins' for cat in data['data'][0].get('categories', [])):
             return ["Bukkit", "Spigot", "Paper"]

        # Haal bestanden op om loaders te bepalen
        files_url = f"https://api.curseforge.com/v1/mods/{mod_id}/files"
        files_response = requests.get(files_url, headers=headers)
        files_response.raise_for_status()
        files_data = files_response.json()

        loaders = set()
        for file in files_data.get('data', []):
            for loader in file.get('gameVersions', []):
                # Filter op bekende loaders, vermijd game-versies
                normalized_loader = loader.strip().upper()
                if normalized_loader in ["FABRIC", "FORGE", "QUILT", "NEOFORGE", "PAPER", "PUFFERFISH", "PURPUR"]:
                    loaders.add(normalized_loader)

        return list(loaders) if loaders else []

    except Exception:
        return []

# -------- GITHUB --------
def get_github_loaders(owner_repo):
    # Kan niet betrouwbaar worden bepaald vanaf GitHub
    return []

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Extract plugin loaders from various platform URLs")
    parser.add_argument("url", help="Plugin URL")
    args = parser.parse_args()

    platform, identifier = detect_platform(args.url)

    loaders = []
    if platform == "modrinth":
        loaders = get_modrinth_loaders(identifier)
    elif platform == "spigot":
        loaders = get_spigot_loaders(identifier)
    elif platform == "hangar":
        loaders = get_hangar_loaders(identifier)
    elif platform == "curseforge":
        # Extra check voor originele URL voor Bukkit-plugins
        if "dev.bukkit.org" in args.url or "bukkit-plugins" in args.url:
             loaders = ["Bukkit", "Spigot", "Paper"]
        else:
            loaders = get_curseforge_loaders(identifier)
    elif platform == "github":
        loaders = get_github_loaders(identifier)
    else:
        print("Unsupported URL", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(loaders))

if __name__ == "__main__":
    main()
