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
def _extract_game_versions(gv_input):
    if not gv_input:
        return []
    if isinstance(gv_input, list):
        items = gv_input
    else:
        items = [str(gv_input)]

    result = []
    for item in items:
        matches = re.findall(r'1\.\d+(?:\.\d+)?', str(item))
        for m in matches:
            if m not in result:
                result.append(m)
    return result

def _clean_plugin_version_from_name(name):
    if not name:
        return ''
    cleaned = name.strip()
    cleaned = re.sub(r'\.(jar|zip)$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'jar$', '', cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    m = re.search(r'(?:^|[_\s\-\/]|[vV]|release-|rel-)(\d+(?:\.\d+)*(?:[-_.][a-zA-Z0-9]+)*)$', cleaned)
    if m:
        extracted = m.group(1).strip()
        if any(c.isdigit() for c in extracted):
            return extracted
    return cleaned

def _is_just_game_version(s):
    if not s:
        return False
    clean = str(s).strip()
    clean = re.sub(r'\.(?:jar|zip)$', '', clean, flags=re.IGNORECASE).strip()
    clean = re.sub(r'^\[(.*)\]$', r'\1', clean).strip()
    return bool(re.fullmatch(r'(?:MC|Minecraft|CB|CraftBukkit|Spigot|Paper)?[\s_-]*v?(?:1\.(?:[5-9]|[1-9]\d)(?:\.\d+)?|26\.\d+)', clean, re.IGNORECASE))

def _resolve_file_plugin_version(file_obj):
    candidates = [
        file_obj.get('displayName'),
        file_obj.get('fileName'),
        file_obj.get('filename'),
        file_obj.get('name')
    ]
    for cand in candidates:
        if not cand:
            continue
        cand_str = str(cand).strip()
        if _is_just_game_version(cand_str):
            continue
        cleaned = _clean_plugin_version_from_name(cand_str)
        if cleaned:
            return cleaned
    return ''

def _get_bukkitdev_file_sort_key(f):
    dr = f.get("dateReleased") or ""
    m = re.search(r'/Date\((-?\d+)', dr)
    if m:
        val = int(m.group(1))
        if val > 0:
            return val
    m2 = re.search(r'/(\d+)(?:/|\b)', f.get("downloadUrl") or f.get("fileUrl") or "")
    if m2:
        return int(m2.group(1))
    return f.get("id", 0)

def _process_bukkitdev_file(f, pin_format, seen, versions_list):
    file_name = _resolve_file_plugin_version(f)
    gvs = _extract_game_versions(f.get("gameVersion"))
    if pin_format:
        if file_name and gvs:
            for gv in gvs:
                _append_unique(f"{file_name} ({gv})", seen, versions_list)
        elif file_name:
            _append_unique(file_name, seen, versions_list)
        elif gvs:
            for gv in gvs:
                _append_unique(gv, seen, versions_list)
    else:
        for gv in gvs:
            _append_unique(gv, seen, versions_list)

def _scrape_bukkitdev_files(slug):
    try:
        url = f"https://dev.bukkit.org/projects/{slug}/files"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return []
        rows = re.findall(r'<tr class="project-file-list-item">.*?</tr>', r.text, re.DOTALL)
        files = []
        for row in rows:
            name_match = re.search(r'<a[^>]+data-action="file-link"[^>]*>([^<]+)</a>', row) or re.search(r'<a class="overflow-tip"[^>]*>([^<]+)</a>', row)
            name = name_match.group(1).strip() if name_match else ""
            fid_match = re.search(r'/files/(\d+)', row)
            fid = int(fid_match.group(1)) if fid_match else 0
            td_gv = re.search(r'<td[^>]*class="[^"]*game-version[^"]*"[^>]*>(.*?)</td>', row, re.DOTALL)
            gvs = []
            if td_gv:
                for gv in re.findall(r'1\.\d+(?:\.\d+)?', td_gv.group(1)):
                    if gv not in gvs:
                        gvs.append(gv)
            if name or gvs:
                files.append({"name": name, "id": fid, "gameVersion": gvs})
        return files
    except Exception:
        return []

def get_bukkitdev_game_versions(slug, pin_format=False):
    try:
        scraped_files = _scrape_bukkitdev_files(slug)
        if scraped_files:
            scraped_files = sorted(scraped_files, key=lambda x: x.get("id", 0), reverse=True)
            versions_list = []
            seen = set()
            for f in scraped_files:
                _process_bukkitdev_file(f, pin_format, seen, versions_list)
            if not pin_format:
                return sorted(versions_list)
            return versions_list

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
        # Sort files descending by release date or file ID so newest releases are first
        files = sorted(files, key=_get_bukkitdev_file_sort_key, reverse=True)
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
def _process_curseforge_file_object(file_obj, pin_format, seen, versions_list):
    file_name = _resolve_file_plugin_version(file_obj)
    raw_gv = file_obj.get('gameVersions') or file_obj.get('gameVersion')
    gvs = _extract_game_versions(raw_gv)

    if pin_format:
        if file_name and gvs:
            for gv in gvs:
                _append_unique(f"{file_name} ({gv})", seen, versions_list)
        elif file_name:
            _append_unique(file_name, seen, versions_list)
        elif gvs:
            for gv in gvs:
                _append_unique(gv, seen, versions_list)
    else:
        for gv in gvs:
            _append_unique(gv, seen, versions_list)

def _group_curseforge_indexes(indexes):
    grouped = {}
    order = []
    for idx in indexes:
        fid = idx.get('fileId') or idx.get('filename')
        if not fid:
            continue
        if fid not in grouped:
            order.append(fid)
            grouped[fid] = {
                'id': idx.get('fileId', 0),
                'displayName': idx.get('displayName'),
                'fileName': idx.get('fileName') or idx.get('filename'),
                'filename': idx.get('filename'),
                'gameVersions': []
            }
        gv = idx.get('gameVersion')
        if gv and gv not in grouped[fid]['gameVersions']:
            grouped[fid]['gameVersions'].append(gv)
    res = [grouped[fid] for fid in order]
    return sorted(res, key=lambda x: x.get('id', 0), reverse=True)

def _parse_curseforge_versions(mod_data, pin_format):
    versions_list = []
    seen = set()
    for mod in mod_data:
        files = mod.get('latestFiles', [])
        if files:
            files = sorted(files, key=lambda x: x.get('id', 0), reverse=True)
            for file_obj in files:
                _process_curseforge_file_object(file_obj, pin_format, seen, versions_list)
        else:
            indexes = mod.get('latestFilesIndexes', [])
            grouped_files = _group_curseforge_indexes(indexes)
            for file_obj in grouped_files:
                _process_curseforge_file_object(file_obj, pin_format, seen, versions_list)
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
        return (0, [])
    clean = re.sub(r'^[vV]', '', str(v)).strip()
    has_leading_digit = bool(re.match(r'^\d', clean))
    parts = re.split(r'[-+.]', clean)
    key = []
    for p in parts:
        if p.isdigit():
            key.append((1, int(p)))
        else:
            key.append((0, p.lower()))
    priority = 1 if has_leading_digit else 0
    return (priority, key)

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

    # Sort groups descending by plugin version key so newest versions appear first
    groups = sorted(groups, key=lambda g: _parse_version_key(g['p_ver']), reverse=True)

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
