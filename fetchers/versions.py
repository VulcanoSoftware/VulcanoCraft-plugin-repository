import argparse
import json
import os
import re
import requests
import sys
from urllib.parse import urlparse

CURSEFORGE_API_KEY = os.environ.get("CURSEFORGE_API_KEY")

# -------- MODRINTH --------
def _process_modrinth_pin_entry(ver_num, game_vers, seen, versions_list):
    if ver_num and game_vers:
        for gv in game_vers:
            _append_unique(f"{ver_num} ({gv})", seen, versions_list)
    elif ver_num:
        _append_unique(ver_num, seen, versions_list)
    elif game_vers:
        for gv in game_vers:
            _append_unique(gv, seen, versions_list)

def _parse_modrinth_pin_versions(data, server_platforms):
    versions_list = []
    seen = set()
    for v in data:
        loaders = [loader.lower() for loader in v.get("loaders", [])]
        if not any(loader in server_platforms for loader in loaders):
            continue
        ver_num = (v.get("version_number") or "").strip().lstrip('v')
        game_vers = v.get("game_versions", [])
        _process_modrinth_pin_entry(ver_num, game_vers, seen, versions_list)
    return versions_list

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
def get_spigot_game_versions(url, pin_format=False):
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
        tested_versions = data.get('testedVersions', [])

        if not pin_format:
            return sorted(tested_versions) if tested_versions else []

        versions_url = f"https://api.spiget.org/v2/resources/{resource_id}/versions?size=100&sort=-id"
        v_response = requests.get(versions_url)
        if v_response.status_code != 200:
            return []

        versions_data = v_response.json()
        if not isinstance(versions_data, list):
            return []

        versions_list = []
        seen = set()

        for v in versions_data:
            ver_name = (v.get('name') or '').strip().lstrip('v')
            if not ver_name:
                continue
            if tested_versions:
                for gv in tested_versions:
                    _append_unique(f"{ver_name} ({gv})", seen, versions_list)
            else:
                _append_unique(ver_name, seen, versions_list)

        return versions_list
    except Exception:
        return None

# -------- HANGAR --------
def _append_unique(entry, seen, versions_list):
    if entry and entry not in seen:
        seen.add(entry)
        versions_list.append(entry)

def _extract_hangar_deps(platform_deps):
    gv_list = []
    for versions in platform_deps.values():
        for version in versions:
            if version not in gv_list:
                gv_list.append(version)
    return gv_list

def _process_hangar_pin_version(ver_name, gv_list, seen, versions_list):
    if ver_name and gv_list:
        for gv in gv_list:
            _append_unique(f"{ver_name} ({gv})", seen, versions_list)
    elif ver_name:
        _append_unique(ver_name, seen, versions_list)
    elif gv_list:
        for gv in gv_list:
            _append_unique(gv, seen, versions_list)

def _process_hangar_version(v, pin_format, seen, versions_list):
    ver_name = (v.get("name") or "").strip().lstrip('v')
    gv_list = _extract_hangar_deps(v.get("platformDependencies", {}))

    if pin_format:
        _process_hangar_pin_version(ver_name, gv_list, seen, versions_list)
    else:
        for gv in gv_list:
            _append_unique(gv, seen, versions_list)

def get_hangar_game_versions(combined_slug, pin_format=False):
    try:
        limit = 25
        offset = 0
        versions_list = []
        seen = set()
        
        while True:
            url = f"https://hangar.papermc.io/api/v1/projects/{combined_slug}/versions?limit={limit}&offset={offset}"
            
            response = requests.get(url)
            response.raise_for_status()
                
            data = response.json()
            if not data.get("result"):
                break
                
            for v in data["result"]:
                _process_hangar_version(v, pin_format, seen, versions_list)
            
            pagination = data.get("pagination", {})
            if offset + limit >= pagination.get("count", 0):
                break
                
            offset += limit
        
        if not pin_format:
            return sorted(versions_list)
        return versions_list
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
def _process_bukkitdev_file(f, pin_format, seen, versions_list):
    file_name = (f.get("name") or "").strip()
    gv = f.get("gameVersion")
    if pin_format:
        entry = ""
        if file_name and gv:
            entry = f"{file_name} ({gv})"
        elif file_name:
            entry = file_name
        elif gv:
            entry = gv
        if entry and entry not in seen:
            seen.add(entry)
            versions_list.append(entry)
    else:
        if gv and re.match(r'^1\.\d+(\.\d+)?$', gv):
            if gv not in seen:
                seen.add(gv)
                versions_list.append(gv)

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
        # Sort files descending by id to get newest releases first
        files = sorted(files, key=lambda f: f.get("id", 0), reverse=True)
        versions_list = []
        seen = set()
        for f in files:
            _process_bukkitdev_file(f, pin_format, seen, versions_list)
        if not pin_format:
            return sorted(versions_list)
        return versions_list
    except Exception:
        return []

# -------- CURSEFORGE --------
def _process_curseforge_file_index(version, pin_format, seen, versions_list):
    file_name = (version.get('filename') or version.get('name') or '').strip()
    game_version = version.get('gameVersion')
    if pin_format:
        entry = ""
        if file_name and game_version:
            entry = f"{file_name} ({game_version})"
        elif file_name:
            entry = file_name
        elif game_version:
            entry = game_version
        _append_unique(entry, seen, versions_list)
    else:
        if game_version and re.match(r'^1\.\d+(\.\d+)?$', game_version):
            _append_unique(game_version, seen, versions_list)

def _parse_curseforge_versions(mod_data, pin_format):
    versions_list = []
    seen = set()
    for mod in mod_data:
        indexes = mod.get('latestFilesIndexes', [])
        indexes = sorted(indexes, key=lambda x: x.get('fileId', 0), reverse=True)
        for version in indexes:
            _process_curseforge_file_index(version, pin_format, seen, versions_list)
    if not pin_format:
        return sorted(versions_list)
    return versions_list

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

# -------- SORTING PIN VERSIONS --------
def _parse_version_key(v):
    if not v:
        return []
    clean = re.sub(r'^[vV]', '', str(v)).strip()
    parts = re.split(r'[-+.]', clean)
    key = []
    for p in parts:
        if p.isdigit():
            key.append((0, int(p)))
        else:
            key.append((1, p))
    return key

def _sort_pin_versions(versions_list):
    if not versions_list:
        return []
    groups = []
    group_map = {}
    for item in versions_list:
        match = re.match(r'^(.+?)\s*\((.+?)\)$', item)
        if match:
            p_ver = match.group(1).strip()
            g_ver = match.group(2).strip()
        else:
            p_ver = item.strip()
            g_ver = None

        if p_ver not in group_map:
            group_obj = {'p_ver': p_ver, 'g_vers': []}
            group_map[p_ver] = group_obj
            groups.append(group_obj)

        if g_ver and g_ver not in group_map[p_ver]['g_vers']:
            group_map[p_ver]['g_vers'].append(g_ver)

    result = []
    for grp in groups:
        p_ver = grp['p_ver']
        g_vers = grp['g_vers']
        if g_vers:
            sorted_g_vers = sorted(g_vers, key=_parse_version_key, reverse=True)
            for gv in sorted_g_vers:
                result.append(f"{p_ver} ({gv})")
        else:
            result.append(p_ver)
    return result

# -------- MAIN --------
def _fetch_platform_versions(platform, identifier, pin_format):
    res = None
    if platform == "modrinth":
        res = get_modrinth_server_game_versions(identifier, pin_format=pin_format)
    elif platform == "spigot":
        res = get_spigot_game_versions(identifier, pin_format=pin_format)
    elif platform == "hangar":
        res = get_hangar_game_versions(identifier, pin_format=pin_format)
    elif platform == "curseforge":
        res = get_curseforge_game_versions(identifier, pin_format=pin_format)
    elif platform == "bukkitdev":
        res = get_bukkitdev_game_versions(identifier, pin_format=pin_format)
    elif platform == "github":
        res = get_github_game_versions(identifier)
    elif platform == "planetminecraft":
        res = get_planetminecraft_game_versions(identifier)

    if pin_format and isinstance(res, list):
        return _sort_pin_versions(res)
    return res

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
