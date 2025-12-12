import argparse
import re
import requests
import sys
from urllib.parse import urlparse

# -------- MODRINTH --------
def get_modrinth_server_game_versions(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}/version"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        server_platforms = {"purpur", "paper", "spigot", "bukkit", "neoforge"}
        platform_priority = {"purpur": 5, "paper": 4, "spigot": 3, "bukkit": 2, "neoforge": 1}

        game_versions_dict = {}

        for v in data:
            loaders = [loader.lower() for loader in v.get("loaders", [])]
            relevant_loaders = [loader for loader in loaders if loader in server_platforms]
            if not relevant_loaders:
                continue
            best_loader = max(relevant_loaders, key=lambda loader: platform_priority[loader])
            for gv in v.get("game_versions", []):
                if gv in game_versions_dict:
                    if platform_priority[best_loader] > platform_priority[game_versions_dict[gv]]:
                        game_versions_dict[gv] = best_loader
                else:
                    game_versions_dict[gv] = best_loader

        return sorted(game_versions_dict.keys())
    except Exception:
        return None

# -------- SPIGOT --------
def get_spigot_game_versions(url):
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
        versions = data.get('testedVersions', [])
        
        return sorted(versions) if versions else []
    except Exception:
        return None

# -------- HANGAR --------
def get_hangar_game_versions(combined_slug):
    try:
        limit = 25
        offset = 0
        game_versions = set()
        
        while True:
            url = f"https://hangar.papermc.io/api/v1/projects/{combined_slug}/versions?limit={limit}&offset={offset}"
            
            response = requests.get(url)
            response.raise_for_status()
                
            data = response.json()
            
            if not data.get("result"):
                break
                
            for v in data["result"]:
                platform_deps = v.get("platformDependencies", {})
                for platform_name, versions in platform_deps.items():
                    for version in versions:
                        game_versions.add(version)
            
            pagination = data.get("pagination", {})
            if offset + limit >= pagination.get("count", 0):
                break
                
            offset += limit
        
        return sorted(game_versions)
    except Exception:
        return None

# -------- BUKKITDEV / SERVERMODS --------
def get_bukkitdev_game_versions(slug):
    try:
        search_url = f"https://api.curseforge.com/servermods/projects?search={slug}"
        search_response = requests.get(search_url)
        if search_response.status_code != 200:
            return []
        projects = search_response.json()
        if not isinstance(projects, list) or not projects:
            return []
        project = None
        for p in projects:
            if p.get("slug") == slug:
                project = p
                break
        if project is None:
            project = projects[0]
        project_id = project.get("id")
        if not project_id:
            return []
        files_url = f"https://api.curseforge.com/servermods/files?projectIds={project_id}"
        files_response = requests.get(files_url)
        if files_response.status_code != 200:
            return []
        files = files_response.json()
        if not isinstance(files, list):
            return []
        versions = set()
        for f in files:
            gv = f.get("gameVersion")
            if gv and re.match(r'^1\.\d+(\.\d+)?$', gv):
                versions.add(gv)
        return sorted(versions) if versions else []
    except Exception:
        return []

# -------- CURSEFORGE --------
def get_curseforge_game_versions(url):
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) < 3:
            return []
        
        category = path_parts[1]
        project_slug = path_parts[2]

        if category == 'bukkit-plugins':
            return get_bukkitdev_game_versions(project_slug)
        
        class_id = 6 if category == 'mc-mods' else 4471 if category == 'modpacks' else None
        if not class_id:
            return []
        
        api_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&slug={project_slug}&classId={class_id}"
        
        headers = {
            'Accept': 'application/json',
            'x-api-key': '$2a$10$bL4bIL5pUWqfcO7KQtnMReakwtfHbNKh6v1uTpKlzhwoueEJQnPnm'
        }
        
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            return []
        
        data = response.json()
        if not data.get('data'):
            return []
        
        versions = set()
        for mod in data['data']:
            for version in mod.get('latestFilesIndexes', []):
                game_version = version.get('gameVersion')
                if game_version and re.match(r'^1\.\d+(\.\d+)?$', game_version):
                    versions.add(game_version)
        
        return sorted(versions) if versions else []
    except Exception:
        return []

# -------- GITHUB --------
def get_github_game_versions(repo_slug):
    try:
        return []
    except Exception:
        return []

# -------- PLATFORM DETECTIE --------
def detect_platform(url):
    try:
        parsed = urlparse(url)
        host = parsed.netloc

        if "modrinth.com" in host:
            match = re.search(r"/(plugin|mod)/([^/]+)/?", parsed.path)
            if match:
                return "modrinth", match.group(2)

        elif "spigotmc.org" in host:
            return "spigot", url

        elif "hangar.papermc.io" in host:
            match = re.search(r"/([^/]+)/([^/]+)/?$", parsed.path)
            if match:
                author = match.group(1)
                project = match.group(2)
                return "hangar", f"{author}/{project}"

        elif "dev.bukkit.org" in host:
            match = re.search(r"/projects/([^/]+)/?", parsed.path)
            if match:
                return "bukkitdev", match.group(1)

        elif "github.com" in host:
            parts = parsed.path.strip('/').split('/')
            if len(parts) >= 2:
                return "github", f"{parts[0]}/{parts[1]}"

        elif "curseforge.com" in host:
            return "curseforge", url

        return None, None
    except Exception:
        return None, None

# -------- MAIN --------
def main():
    parser = argparse.ArgumentParser(description="Print supported Minecraft versions of a plugin")
    parser.add_argument("url", nargs="?", help="Plugin URL from Modrinth, SpigotMC, or Hangar")
    args = parser.parse_args()

    if not args.url:
        args.url = input("Geef een plugin URL op: ").strip()

    platform, identifier = detect_platform(args.url)
    if not platform:
        print("ongeldige url", file=sys.stderr)
        sys.exit(1)

    if platform == "modrinth":
        game_versions = get_modrinth_server_game_versions(identifier)
    elif platform == "spigot":
        game_versions = get_spigot_game_versions(identifier)
    elif platform == "hangar":
        game_versions = get_hangar_game_versions(identifier)
    elif platform == "curseforge":
        game_versions = get_curseforge_game_versions(identifier)
    elif platform == "bukkitdev":
        game_versions = get_bukkitdev_game_versions(identifier)
    elif platform == "github":
        game_versions = get_github_game_versions(identifier)
    else:
        print("ongeldige url", file=sys.stderr)
        sys.exit(1)

    if game_versions is None:
        print("", file=sys.stderr)
        sys.exit(1)
    elif game_versions:
        print(" ".join(game_versions))
    else:
        print("")

if __name__ == "__main__":
    main()
