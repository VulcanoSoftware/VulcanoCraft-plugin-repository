import argparse
import os
import re
import requests
import sys
from urllib.parse import urlparse, urlunparse

HTML_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

CURSEFORGE_API_KEY = os.environ.get("CURSEFORGE_API_KEY")

# -------- MODRINTH --------
def get_modrinth_icon(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        icon_url = data.get("icon_url")
        if icon_url:
            parsed = urlparse(icon_url)
            return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        return None
    except Exception:
        return None

# -------- SPIGOT --------
def get_spigot_icon(url):
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
        icon = data.get('icon')
        if icon and 'url' in icon:
            icon_url = icon['url']
            if not icon_url.startswith('http'):
                icon_url = f"https://www.spigotmc.org/{icon_url}"
            if '?' in icon_url:
                icon_url = icon_url.split('?')[0]
            return icon_url
        
        return None
    except Exception:
        return None

# -------- HANGAR --------
def get_hangar_icon(combined_slug):
    try:
        url = f"https://hangar.papermc.io/api/v1/projects/{combined_slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        avatar_url = data.get("avatarUrl")
        if avatar_url:
            parsed = urlparse(avatar_url)
            return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        return None
        
    except Exception:
        return None

def _extract_meta_image(text):
    pattern = r'<meta[^>]+(?=[^>]*(?:name|property)=["\']og:image["\'])(?=[^>]*content=["\']([^"\']+)["\'])'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1)
    pattern_twitter = r'<meta[^>]+(?=[^>]*(?:name|property)=["\']twitter:image["\'])(?=[^>]*content=["\']([^"\']+)["\'])'
    match = re.search(pattern_twitter, text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def _get_curseforge_mod(project_slug, class_id):
    try:
        api_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&slug={project_slug}&classId={class_id}"
        headers = {
            "Accept": "application/json",
            "x-api-key": CURSEFORGE_API_KEY,
        }
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            return None
        data = response.json()
        if not data.get("data"):
            return None
        return data["data"][0]
    except Exception:
        return None

def _get_servermods_project(slug):
    try:
        url = f"https://api.curseforge.com/servermods/projects?search={slug}"
        response = requests.get(url)
        if response.status_code != 200:
            return None
        projects = response.json()
        if not isinstance(projects, list) or not projects:
            if "-" not in slug and slug.endswith("plate"):
                alt_slug = slug[:-5] + "-plate"
                url = f"https://api.curseforge.com/servermods/projects?search={alt_slug}"
                response = requests.get(url)
                if response.status_code != 200:
                    return None
                projects = response.json()
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

def _extract_planetminecraft_avatar(text):
    try:
        pattern = r'<img[^>]*class=["\']avatar["\'][^>]*src=["\']([^"\']+)["\']'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    except Exception:
        return None

def _search_modrinth_icon(name_hint):
    try:
        if not name_hint:
            return None
        search_url = "https://api.modrinth.com/v2/search"
        params = {"query": name_hint}
        response = requests.get(search_url, params=params)
        if response.status_code != 200:
            return None
        data = response.json()
        hits = data.get("hits") or []
        if not hits:
            return None
        slug = hits[0].get("slug")
        if not slug:
            return None
        return get_modrinth_icon(slug)
    except Exception:
        return None

def get_bukkitdev_icon(slug):
    try:
        project_slug = slug
        try:
            project = _get_servermods_project(slug)
            if project and project.get("slug"):
                project_slug = project.get("slug")
        except Exception:
            project_slug = slug
        mod = _get_curseforge_mod(project_slug, 5)
        if mod:
            logo = mod.get("logo")
            if logo:
                icon_url = logo.get("thumbnailUrl") or logo.get("url")
                if icon_url and "?" in icon_url:
                    icon_url = icon_url.split("?", 1)[0]
                if icon_url:
                    return icon_url
            authors = mod.get("authors") or []
            if authors:
                avatar_url = authors[0].get("avatarUrl")
                if avatar_url:
                    if "?" in avatar_url:
                        avatar_url = avatar_url.split("?", 1)[0]
                    return avatar_url
        page_url = f"https://dev.bukkit.org/projects/{project_slug}"
        response = requests.get(page_url, headers=HTML_HEADERS)
        if response.status_code != 200:
            return None
        icon_url = _extract_meta_image(response.text)
        if icon_url and "?" in icon_url:
            icon_url = icon_url.split("?", 1)[0]
        return icon_url
    except Exception:
        return None

# -------- CURSEFORGE --------
def get_curseforge_icon(url):
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) < 3:
            return None
        
        category = path_parts[1]
        project_slug = path_parts[2]

        class_id = 5 if category == 'bukkit-plugins' else 6 if category == 'mc-mods' else 4471 if category == 'modpacks' else None
        if class_id:
            mod = _get_curseforge_mod(project_slug, class_id)
            if mod:
                logo = mod.get("logo")
                if logo:
                    icon_url = logo.get("thumbnailUrl") or logo.get("url")
                    if icon_url and '?' in icon_url:
                        icon_url = icon_url.split('?', 1)[0]
                    if icon_url:
                        return icon_url

        if category == 'bukkit-plugins':
            try:
                response = requests.get(url, headers=HTML_HEADERS)
                if response.status_code != 200:
                    return None
                icon_url = _extract_meta_image(response.text)
                if icon_url and '?' in icon_url:
                    icon_url = icon_url.split('?', 1)[0]
                if icon_url:
                    return icon_url
            except Exception:
                return None

        return None
    except Exception:
        return None

def get_planetminecraft_icon(url):
    try:
        icon_url = None
        try:
            response = requests.get(url, headers=HTML_HEADERS)
            if response.status_code == 200:
                text = response.text
                icon_url = _extract_planetminecraft_avatar(text)
                if not icon_url:
                    icon_url = _extract_meta_image(text)
        except Exception:
            icon_url = None
        if not icon_url:
            parsed = urlparse(url)
            parts = [p for p in parsed.path.strip("/").split("/") if p]
            slug = parts[-1] if parts else ""
            if slug:
                base = slug.replace("-", " ")
                if base.lower().endswith(" datapack"):
                    base = base[: -len(" datapack")].strip()
                icon_url = _search_modrinth_icon(base)
        if icon_url and '?' in icon_url:
            icon_url = icon_url.split('?', 1)[0]
        return icon_url
    except Exception:
        return ""

# -------- GITHUB --------
def get_github_icon(repo_slug):
    try:
        if '/' not in repo_slug:
            return None
        owner, repo = repo_slug.split('/', 1)
        url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {"Accept": "application/vnd.github+json"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None
        data = response.json()
        owner_data = data.get("owner") or {}
        avatar_url = owner_data.get("avatar_url")
        if avatar_url and '?' in avatar_url:
            avatar_url = avatar_url.split('?', 1)[0]
        return avatar_url
    except Exception:
        return None

# -------- PLATFORM DETECTION --------
def detect_platform(url):
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()

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
def main():
    parser = argparse.ArgumentParser(description="Extract plugin icon URL from Modrinth, SpigotMC, or Hangar URLs")
    parser.add_argument("url", nargs="?", help="Plugin URL from Modrinth, SpigotMC, or Hangar")
    args = parser.parse_args()

    if not args.url:
        args.url = input("Enter a plugin URL: ").strip()

    platform, identifier = detect_platform(args.url)
    if not platform:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if platform == "modrinth":
        icon_url = get_modrinth_icon(identifier)
    elif platform == "spigot":
        icon_url = get_spigot_icon(identifier)
    elif platform == "hangar":
        icon_url = get_hangar_icon(identifier)
    elif platform == "curseforge":
        icon_url = get_curseforge_icon(identifier)
    elif platform == "bukkitdev":
        icon_url = get_bukkitdev_icon(identifier)
    elif platform == "github":
        icon_url = get_github_icon(identifier)
    elif platform == "planetminecraft":
        icon_url = get_planetminecraft_icon(identifier)
    else:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if icon_url is None:
        print("", file=sys.stderr)
        sys.exit(1)
    else:
        print(icon_url)

if __name__ == "__main__":
    main()
