import argparse
import re
import requests
import sys
from urllib.parse import urlparse

# -------- MODRINTH --------
def get_modrinth_title(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("title")
    except Exception:
        return None

# -------- SPIGOT --------
def get_spigot_title(url):
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
        return data.get('name')
    except Exception:
        return None

# -------- HANGAR --------
def get_hangar_title(combined_slug):
    try:
        url = f"https://hangar.papermc.io/api/v1/projects/{combined_slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("name")
    except Exception:
        return None

def _get_servermods_project(slug):
    try:
        api_url = f"https://api.curseforge.com/servermods/projects?search={slug}"
        response = requests.get(api_url)
        if response.status_code != 200:
            return None
        projects = response.json()
        if not isinstance(projects, list) or not projects:
            if "-" not in slug and slug.endswith("plate"):
                alt_slug = slug[:-5] + "-plate"
                api_url = f"https://api.curseforge.com/servermods/projects?search={alt_slug}"
                response = requests.get(api_url)
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

# -------- BUKKITDEV / SERVERMODS --------
def get_bukkitdev_title(slug):
    project = _get_servermods_project(slug)
    if not project:
        return None
    return project.get("name")

# -------- CURSEFORGE --------
def get_curseforge_title(url):
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) < 3:
            return None
        
        category = path_parts[1]
        project_slug = path_parts[2]

        if category == 'bukkit-plugins':
            return get_bukkitdev_title(project_slug)
        
        class_id = 6 if category == 'mc-mods' else 4471 if category == 'modpacks' else None
        if not class_id:
            return None
        
        api_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&slug={project_slug}&classId={class_id}"
        
        headers = {
            'Accept': 'application/json',
            'x-api-key': '$2a$10$bL4bIL5pUWqfcO7KQtnMReakwtfHbNKh6v1uTpKlzhwoueEJQnPnm'
        }
        
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            return None
        
        data = response.json()
        if data.get('data'):
            return data['data'][0].get('name')
        
        return None
    except Exception:
        return None

def _extract_meta_content(text, meta_name):
    try:
        pattern = rf'<meta[^>]+(?:name|property)="{meta_name}"[^>]+content="([^"]+)"'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    except Exception:
        return None

def get_planetminecraft_title(url):
    try:
        response = requests.get(url)
        title = None
        if response.status_code == 200:
            text = response.text
            title = _extract_meta_content(text, "og:title")
            if title is None:
                title = _extract_meta_content(text, "title")
            if title is None:
                match = re.search(r"<title>([^<]+)</title>", text, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
        if title is None:
            parsed = urlparse(url)
            parts = [p for p in parsed.path.strip("/").split("/") if p]
            slug = parts[-1] if parts else ""
            if slug:
                words = slug.replace("-", " ").split()
                return " ".join(w.capitalize() for w in words)
            return ""
        return title
    except Exception:
        parsed = urlparse(url)
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        slug = parts[-1] if parts else ""
        if slug:
            words = slug.replace("-", " ").split()
            return " ".join(w.capitalize() for w in words)
        return ""

# -------- GITHUB --------
def get_github_title(repo_slug):
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
        return data.get("name") or data.get("full_name")
    except Exception:
        return None

# -------- PLATFORM DETECTION --------
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
def main():
    parser = argparse.ArgumentParser(description="Extract plugin title from Modrinth, SpigotMC, or Hangar URLs")
    parser.add_argument("url", nargs="?", help="Plugin URL from Modrinth, SpigotMC, or Hangar")
    args = parser.parse_args()

    if not args.url:
        args.url = input("Enter a plugin URL: ").strip()

    platform, identifier = detect_platform(args.url)
    if not platform:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if platform == "modrinth":
        title = get_modrinth_title(identifier)
    elif platform == "spigot":
        title = get_spigot_title(identifier)
    elif platform == "hangar":
        title = get_hangar_title(identifier)
    elif platform == "curseforge":
        title = get_curseforge_title(identifier)
    elif platform == "bukkitdev":
        title = get_bukkitdev_title(identifier)
    elif platform == "github":
        title = get_github_title(identifier)
    elif platform == "planetminecraft":
        title = get_planetminecraft_title(identifier)
    else:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if title is None:
        print("", file=sys.stderr)
        sys.exit(1)
    else:
        print(title)

if __name__ == "__main__":
    main()
