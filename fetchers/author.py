import argparse
import html
import os
import re
import requests
import sys
from urllib.parse import urlparse

HTML_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

CURSEFORGE_API_KEY = os.environ.get(
    "CURSEFORGE_API_KEY",
    "$2a$10$bL4bIL5pUWqfcO7KQtnMReakwtfHbNKh6v1uTpKlzhwoueEJQnPnm",
)

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
        
        authors = []
        for member in team_data:
            if 'user' in member and isinstance(member['user'], dict):
                username = member['user'].get("username")
                if username:
                    authors.append(username)
        
        return " ".join(authors) if authors else None
        
    except Exception:
        return None

# -------- SPIGOT --------
def get_spigot_author(url):
    try:
        match = re.search(r'/resources/[^/]+\.(\d+)/?', url)
        if not match:
            return None
        
        resource_id = match.group(1)
        api_url = f"https://api.spiget.org/v2/resources/{resource_id}/author"
        
        response = requests.get(api_url)
        if response.status_code != 200:
            return None
        
        data = response.json()
        return data.get('name')
    except Exception:
        return None

# -------- HANGAR --------
def get_hangar_author(combined_slug):
    try:
        parts = combined_slug.split('/')
        if len(parts) >= 1:
            return parts[0]
        return None
    except Exception:
        return None

def _extract_meta_content(text, meta_name):
    try:
        pattern = r'<meta[^>]+(?=[^>]*(?:name|property)=["\']' + re.escape(meta_name) + r'["\'])(?=[^>]*content=["\']([^"\']+)["\'])'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return html.unescape(match.group(1).strip())
        return None
    except Exception:
        return None

def _extract_author_from_html(text):
    try:
        author = _extract_meta_content(text, "author")
        if author:
            return author
        author = _extract_meta_content(text, "article:author")
        if author:
            return author
        json_match = re.search(r'"author"\s*:\s*\{\s*"@type"\s*:\s*"(?:Person|Organization)"\s*,\s*"name"\s*:\s*"([^"]+)"', text, re.IGNORECASE)
        if json_match:
            return html.unescape(json_match.group(1).strip())
        by_link = re.search(r'>\s*by\s*<a[^>]*>([^<]+)</a>', text, re.IGNORECASE)
        if by_link:
            return html.unescape(by_link.group(1).strip())
        return None
    except Exception:
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

def get_bukkitdev_author(slug):
    try:
        project = _get_servermods_project(slug)
        project_slug = project.get("slug") if project and project.get("slug") else slug
        mod = _get_curseforge_mod(project_slug, 5)
        if mod:
            authors = mod.get("authors", [])
            if authors:
                name = authors[0].get("name")
                if name:
                    return name
        page_url = f"https://dev.bukkit.org/projects/{project_slug}"
        response = requests.get(page_url, headers=HTML_HEADERS)
        if response.status_code != 200:
            return None
        return _extract_author_from_html(response.text)
    except Exception:
        return None

# -------- CURSEFORGE --------
def get_curseforge_author(url):
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
                authors = mod.get("authors", [])
                if authors:
                    name = authors[0].get("name")
                    if name:
                        return name

        if category == 'bukkit-plugins':
            response = requests.get(url, headers=HTML_HEADERS)
            if response.status_code != 200:
                return None
            return _extract_author_from_html(response.text)

        return None
    except Exception:
        return None

def _extract_planetminecraft_author(text):
    try:
        match = re.search(r'href="/member/[^"]+"[^>]*>([^<]+)</a>', text, re.IGNORECASE)
        if match:
            return html.unescape(match.group(1).strip())
        return None
    except Exception:
        return None

def _search_modrinth_author(name_hint):
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
        return get_modrinth_author(slug)
    except Exception:
        return None

def get_planetminecraft_author(url):
    try:
        author = None
        try:
            response = requests.get(url, headers=HTML_HEADERS)
            if response.status_code == 200:
                text = response.text
                author = _extract_author_from_html(text)
                if not author:
                    author = _extract_planetminecraft_author(text)
        except Exception:
            author = None
        if not author:
            parsed = urlparse(url)
            parts = [p for p in parsed.path.strip("/").split("/") if p]
            slug = parts[-1] if parts else ""
            if slug:
                base = slug.replace("-", " ")
                if base.lower().endswith(" datapack"):
                    base = base[: -len(" datapack")].strip()
                author = _search_modrinth_author(base)
        if not author:
            return ""
        return author
    except Exception:
        return ""

# -------- GITHUB --------
def get_github_author(repo_slug):
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
        return owner_data.get("login")
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
    parser = argparse.ArgumentParser(description="Extract plugin author from Modrinth, SpigotMC, or Hangar URLs")
    parser.add_argument("url", nargs="?", help="Plugin URL from Modrinth, SpigotMC, or Hangar")
    args = parser.parse_args()

    if not args.url:
        args.url = input("Enter a plugin URL: ").strip()

    platform, identifier = detect_platform(args.url)
    if not platform:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if platform == "modrinth":
        author = get_modrinth_author(identifier)
    elif platform == "spigot":
        author = get_spigot_author(identifier)
    elif platform == "hangar":
        author = get_hangar_author(identifier)
    elif platform == "curseforge":
        author = get_curseforge_author(identifier)
    elif platform == "bukkitdev":
        author = get_bukkitdev_author(identifier)
    elif platform == "github":
        author = get_github_author(identifier)
    elif platform == "planetminecraft":
        author = get_planetminecraft_author(identifier)
    else:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if author is None:
        print("", file=sys.stderr)
        sys.exit(1)
    else:
        print(author)

if __name__ == "__main__":
    main()
