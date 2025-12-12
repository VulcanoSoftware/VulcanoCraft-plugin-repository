import sys
import requests
import json
import os
import re


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

VERSION_REGEX = re.compile(r"^\d+(\.\d+){1,2}$")  # match 1.20.1 / 1.20 / 1.8

def looks_like_mc_version(s: str) -> bool:
    return bool(VERSION_REGEX.match(s))

def extract_slug_from_url(url):
    patterns = [
        r"mc-mods/([^/]+)",
        r"modpacks/([^/]+)",
        r"texture-packs/([^/]+)",
        r"worlds/([^/]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


# ---------------------------------------------------------
# Modrinth
# ---------------------------------------------------------

def get_modrinth_loaders(project_id):
    """Haalt de loaders voor een specifiek Modrinth-project op."""
    try:
        response = requests.get(f"https://api.modrinth.com/v2/project/{project_id}")
        response.raise_for_status()
        project_data = response.json()
        return [loader.lower() for loader in project_data.get("loaders", [])]
    except requests.exceptions.RequestException as e:
        print(f"Fout bij het ophalen van Modrinth-projectgegevens: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------
# SpigotMC
# ---------------------------------------------------------

def get_spigotmc_loaders(resource_id):
    """Haalt de loaders voor een specifiek SpigotMC-resource op."""
    try:
        response = requests.get(f"https://api.spiget.org/v2/resources/{resource_id}")
        response.raise_for_status()
        return ["spigot", "bukkit"]  # Al lowercase
    except requests.exceptions.RequestException as e:
        print(f"Fout bij het ophalen van SpigotMC-resourcegegevens: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------
# Hangar (PaperMC)
# ---------------------------------------------------------

def get_hangar_loaders(author, slug):
    """Haalt de loaders voor een specifiek Hangar-project op."""
    try:
        response = requests.get(
            f"https://hangar.papermc.io/api/v1/projects/{author}/{slug}/versions"
        )
        response.raise_for_status()
        versions_data = response.json()

        loaders = set()
        for version in versions_data.get('result', []):
            for dep in version.get('platformDependencies', {}):
                loaders.add(dep.lower())

        return list(loaders)

    except requests.exceptions.RequestException as e:
        print(f"Fout bij het ophalen van Hangar-projectgegevens: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------
# CurseForge — 100% dynamisch, geen hardcoded loaders
# ---------------------------------------------------------

def get_curseforge_loaders(url, api_key):
    """Haalt de loaders voor een specifiek CurseForge-project op (volledig dynamisch)."""
    slug = extract_slug_from_url(url)
    if not slug:
        return []

    headers = {
        'x-api-key': api_key,
        'Accept': 'application/json',
    }

    try:
        # Zoek mod op basis van slug
        params = {'gameId': 432, 'slug': slug, 'classId': 6}
        search_response = requests.get(
            "https://api.curseforge.com/v1/mods/search",
            headers=headers,
            params=params
        )
        search_response.raise_for_status()
        search_data = search_response.json().get('data', [])

        if not search_data:
            return []

        mod_id = next((m['id'] for m in search_data if m.get('slug') == slug), None)
        if not mod_id:
            return []

        # Haal files op
        files_response = requests.get(
            f"https://api.curseforge.com/v1/mods/{mod_id}/files",
            headers=headers
        )
        files_response.raise_for_status()
        files_data = files_response.json().get('data', [])

        loaders = set()

        for file in files_data:

            # Case 1: bestand heeft expliciete loaders
            if "loaders" in file and file["loaders"]:
                for loader in file["loaders"]:
                    loaders.add(loader.lower())
                continue

            # Case 2: gameVersions dynamisch filteren
            if "gameVersions" in file:
                for entry in file["gameVersions"]:
                    e = entry.lower()

                    # Skip Minecraft-versie, Java-versie of OS
                    if looks_like_mc_version(entry):
                        continue
                    if "java" in e:
                        continue
                    if e in ["windows", "linux", "macos"]:
                        continue

                    # ALLES ANDERS = modloader
                    loaders.add(e)

        return list(loaders)

    except requests.exceptions.RequestException as e:
        print(f"Fout bij het ophalen van CurseForge-projectgegevens: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Gebruik: python fetchers/plugin_loaders.py <url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]

    # Modrinth
    if "modrinth.com" in url:
        project_id = url.split('/')[-1]
        loaders = get_modrinth_loaders(project_id)
        print(json.dumps(loaders))
        return

    # SpigotMC
    if "spigotmc.org" in url:
        try:
            resource_id = url.split('.')[-1].split('/')[0]
            loaders = get_spigotmc_loaders(resource_id)
            print(json.dumps(loaders))
        except IndexError:
            print(json.dumps([]))
        return

    # Hangar
    if "hangar.papermc.io" in url:
        parts = url.strip('/').split('/')
        author = parts[-2]
        slug = parts[-1]
        loaders = get_hangar_loaders(author, slug)
        print(json.dumps(loaders))
        return

    # dev.bukkit.org
    if "dev.bukkit.org" in url:
        print(json.dumps(["bukkit", "spigot"]))
        return

    # GitHub
    if "github.com" in url:
        print(json.dumps(["bukkit", "spigot"]))
        return

    # CurseForge
    if "curseforge.com" in url:
        if "bukkit-plugins" in url:
            print(json.dumps(["bukkit", "spigot", "paper"]))
            return
        api_key = "$2a$10$bL4bIL5pUWqfcO7KQtnMReakwtfHbNKh6v1uTpKlzhwoueEJQnPnm"
        loaders = get_curseforge_loaders(url, api_key)
        print(json.dumps(loaders))
        return

    if "planetminecraft.com" in url:
        print(json.dumps(["datapack"]))
        return

    # Onbekende URL → leeg
    print(json.dumps([]))


if __name__ == "__main__":
    main()
