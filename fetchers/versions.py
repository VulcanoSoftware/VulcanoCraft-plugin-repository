import argparse
import json
import os
import re
import requests
import sys
from urllib.parse import urlparse

CURSEFORGE_API_KEY = os.environ.get("CURSEFORGE_API_KEY")

# -------- MODRINTH --------
def _parse_modrinth_pin_versions(data, server_platforms):
    versions_set = set()
    for v in data:
        loaders = [loader.lower() for loader in v.get("loaders", [])]
        if not any(loader in server_platforms for loader in loaders):
            continue
        ver_num = (v.get("version_number") or "").strip().lstrip('v')
        game_vers = v.get("game_versions", [])
        if ver_num and game_vers:
            for gv in game_vers:
                versions_set.add(f"{ver_num} ({gv})")
        elif ver_num:
            versions_set.add(ver_num)
        elif game_vers:
            for gv in game_vers:
                versions_set.add(gv)
    return sorted(versions_set) if versions_set else []

def _parse_modrinth_game_versions(data, server_platforms, platform_priority):
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

def get_modrinth_server_game_versions(slug, pin_format=False):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}/version"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        server_platforms = {"purpur", "paper", "spigot", "bukkit", "neoforge"}
        platform_priority = {"purpur": 5, "paper": 4, "spigot": 3, "bukkit": 2, "neoforge": 1}

        if pin_format:
            return _parse_modrinth_pin_versions(data, server_platforms)
        return _parse_modrinth_game_versions(data, server_platforms, platform_priority)
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
def get_hangar_game_versions(combined_slug, pin_format=False):
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
                ver_name = (v.get("name") or "").strip().lstrip('v')
                platform_deps = v.get("platformDependencies", {})
                gv_list = set()
                for platform_name, versions in platform_deps.items():
                    for version in versions:
                        gv_list.add(version)

                if pin_format:
                    if ver_name and gv_list:
                        for gv in gv_list:
                            game_versions.add(f"{ver_name} ({gv})")
                    elif ver_name:
                        game_versions.add(ver_name)
                    elif gv_list:
                        game_versions.update(gv_list)
                else:
                    game_versions.update(gv_list)
            
            pagination = data.get("pagination", {})
            if offset + limit >= pagination.get("count", 0):
                break
                
            offset += limit
        
        return sorted(game_versions)
    except Exception:
        return None

def _get_servermods_project(slug):
    try:
        search_url = f"https://api.curseforge.com/servermods/projects?search={slug}"
        search_response = requests.get(search_url)
        if search_response.status_code != 200:
            return None
        projects = search_response.json()
        if not isinstance(projects, list) or not projects:
            if "-" not in slug and slug.endswith("plate"):
                alt_slug = slug[:-5] + "-plate"
                search_url = f"https://api.curseforge.com/servermods/projects?search={alt_slug}"
                search_response = requests.get(search_url)
                if search_response.status_code != 200:
                    return None
                projects = search_response.json()
                if not isinstance(projects, list) or not projects:
                    return None
                slug = alt_slug
            else:
                return None
        for p in projects:
            if p.get("slug") == slug:
                return p
        return projects[0]
    except Exception:
        return None

# -------- BUKKITDEV / SERVERMODS --------
def get_bukkitdev_game_versions(slug, pin_format=False):
    try:
        project = _get_servermods_project(slug)
        if not project:
            return []
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
            file_name = (f.get("name") or "").strip()
            gv = f.get("gameVersion")
            if pin_format:
                if file_name and gv:
                    versions.add(f"{file_name} ({gv})")
                elif file_name:
                    versions.add(file_name)
                elif gv:
                    versions.add(gv)
            else:
                if gv and re.match(r'^1\.\d+(\.\d+)?$', gv):
                    versions.add(gv)
        return sorted(versions) if versions else []
    except Exception:
        return []

# -------- CURSEFORGE --------
def _parse_curseforge_versions(mod_data, pin_format):
    versions = set()
    for mod in mod_data:
        for version in mod.get('latestFilesIndexes', []):
            file_name = (version.get('filename') or version.get('name') or '').strip()
            game_version = version.get('gameVersion')
            if pin_format:
                if file_name and game_version:
                    versions.add(f"{file_name} ({game_version})")
                elif file_name:
                    versions.add(file_name)
                elif game_version:
                    versions.add(game_version)
            else:
                if game_version and re.match(r'^1\.\d+(\.\d+)?$', game_version):
                    versions.add(game_version)
    return sorted(versions) if versions else []

def get_curseforge_game_versions(url, pin_format=False):
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) < 3:
            return []
        
        category = path_parts[1]
        project_slug = path_parts[2]

        if category == 'bukkit-plugins':
            return get_bukkitdev_game_versions(project_slug, pin_format=pin_format)
        
        class_id = 6 if category == 'mc-mods' else 4471 if category == 'modpacks' else None
        if not class_id:
            return []
        
        api_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&slug={project_slug}&classId={class_id}"
        headers = {'Accept': 'application/json', 'x-api-key': CURSEFORGE_API_KEY or ''}
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            return []
        
        data = response.json()
        if not data.get('data'):
            return []
        
        return _parse_curseforge_versions(data['data'], pin_format)
    except Exception:
        return []

# -------- GITHUB --------
def get_github_game_versions(repo_slug):
    try:
        return []
    except Exception:
        return []

def get_planetminecraft_game_versions(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return []
        text = response.text
        matches = re.findall(r"1\.\d+(?:\.\d+)?", text)
        versions = sorted(set(matches))
        return versions
    except Exception:
        return []

# -------- PLATFORM DETECTIE --------
def detect_platform(url):
    try:
        parsed = urlparse(url)
        host = parsed.netloc

        if "modrinth.com" in host:
            match = re.search(r"/(plugin|mod|datapack)/([^/]+)/?", parsed.path)
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

        elif "planetminecraft.com" in host:
            return "planetminecraft", url

        return None, None
    except Exception:
        return None, None

# -------- MAIN --------
def _fetch_platform_versions(platform, identifier, pin_format):
    if platform == "modrinth":
        return get_modrinth_server_game_versions(identifier, pin_format=pin_format)
    if platform == "spigot":
        return get_spigot_game_versions(identifier)
    if platform == "hangar":
        return get_hangar_game_versions(identifier, pin_format=pin_format)
    if platform == "curseforge":
        return get_curseforge_game_versions(identifier, pin_format=pin_format)
    if platform == "bukkitdev":
        return get_bukkitdev_game_versions(identifier, pin_format=pin_format)
    if platform == "github":
        return get_github_game_versions(identifier)
    if platform == "planetminecraft":
        return get_planetminecraft_game_versions(identifier)
    return None

def _output_game_versions(game_versions, is_pin_format):
    if game_versions is None:
        if is_pin_format:
            print("[]")
        else:
            print("", file=sys.stderr)
        sys.exit(1)
    if game_versions:
        if is_pin_format:
            print(json.dumps(game_versions))
        else:
            print(" ".join(game_versions))
    else:
        if is_pin_format:
            print("[]")
        else:
            print("")

def main():
    parser = argparse.ArgumentParser(description="Print supported Minecraft versions of a plugin")
    parser.add_argument("url", nargs="?", help="Plugin URL from Modrinth, SpigotMC, or Hangar")
    parser.add_argument("--pin-versions", action="store_true", help="Format output as PluginVersion (GameVersion)")
    args = parser.parse_args()

    url = args.url or input("Geef een plugin URL op: ").strip()
    platform, identifier = detect_platform(url)
    if not platform:
        print("ongeldige url", file=sys.stderr)
        sys.exit(1)

    game_versions = _fetch_platform_versions(platform, identifier, args.pin_versions)
    _output_game_versions(game_versions, args.pin_versions)

if __name__ == "__main__":
    main()
