import argparse
import json
import os
import re
import requests
import sys

# Voeg de bovenliggende map toe aan het systeempad om utils te kunnen importeren
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fetchers.utils import detect_platform

# -------- MODRINTH --------
def get_modrinth_loaders(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return [loader.lower() for loader in data.get("loaders", [])]
    except Exception:
        return []

# -------- SPIGOT --------
def get_spigot_loaders(url):
    # Spigot/Bukkit plugins hebben niet altijd expliciete loaders,
    # dus we gaan uit van de meest voorkomende.
    return ["bukkit", "spigot", "paper"]

# -------- HANGAR --------
def get_hangar_loaders(combined_slug):
    # Speciale behandeling voor Velocity
    if combined_slug.lower() == "papermc/velocity":
        return ["velocity", "waterfall", "paper"]

    try:
        url = f"https://hangar.papermc.io/api/v1/projects/{combined_slug}/versions"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        loaders = set()
        for version_data in data.get("result", []):
            # De 'keys' van platformDependencies zijn de loader namen (bv. "PAPER", "WATERFALL")
            for loader_name in version_data.get("platformDependencies", {}).keys():
                loaders.add(loader_name.lower())
        return sorted(list(loaders))
    except Exception:
        return []

# -------- CURSEFORGE --------
def get_curseforge_bukkit_loaders(slug):
    """Retourneert een standaard lijst van loaders voor Bukkit-gebaseerde plugins."""
    # CurseForge/Bukkit plugins geven niet expliciet hun loaders aan via de API op een consistente manier.
    # We gaan er daarom vanuit dat ze compatibel zijn met de meest gangbare server software.
    return ["bukkit", "spigot", "paper"]

# -------- GITHUB --------
def get_github_loaders(repo_identifier):
    # Het is niet betrouwbaar om loaders van GitHub af te leiden.
    return []

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Extraheer ondersteunde loaders van een plugin.")
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

    loaders = []
    if platform == "modrinth":
        loaders = get_modrinth_loaders(identifier)
    elif platform == "spigot":
        loaders = get_spigot_loaders(identifier)
    elif platform == "hangar":
        loaders = get_hangar_loaders(identifier)
    elif platform == "curseforge":
        loaders = get_curseforge_bukkit_loaders(identifier)
    elif platform == "github":
        loaders = get_github_loaders(identifier)
    else:
        print(f"Platform '{platform}' wordt nog niet ondersteund.", file=sys.stderr)
        sys.exit(1)

    # De output moet altijd een JSON-lijst zijn.
    print(json.dumps(loaders))

if __name__ == "__main__":
    main()
