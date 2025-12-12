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
def get_modrinth_description(slug):
    try:
        url = f"https://api.modrinth.com/v2/project/{slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("description")
    except Exception:
        return None

# -------- SPIGOT --------
def get_spigot_description(url):
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
        return data.get('tag')
    except Exception:
        return None

# -------- HANGAR --------
def get_hangar_description(combined_slug):
    try:
        url = f"https://hangar.papermc.io/api/v1/projects/{combined_slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("description")
    except Exception:
        return None

def _extract_meta_content(text, meta_name):
    try:
        pattern = rf'<meta[^>]+(?:name|property)="{meta_name}"[^>]+content="([^"]+)"'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return html.unescape(match.group(1))
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

# -------- BUKKITDEV / SERVERMODS --------
def get_bukkitdev_description(slug):
    try:
        mod = _get_curseforge_mod(slug, 5)
        if mod:
            summary = mod.get("summary")
            if summary:
                return summary
        page_url = f"https://dev.bukkit.org/projects/{slug}"
        response = requests.get(page_url, headers=HTML_HEADERS)
        if response.status_code != 200:
            return None
        text = response.text
        description = _extract_meta_content(text, "description")
        if description is None:
            description = _extract_meta_content(text, "og:description")
        return description
    except Exception:
        return None

# -------- CURSEFORGE --------
def get_curseforge_description(url):
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
                summary = mod.get("summary")
                if summary:
                    return summary

        if category == 'bukkit-plugins':
            try:
                response = requests.get(url, headers=HTML_HEADERS)
                if response.status_code != 200:
                    return None
                text = response.text
                description = _extract_meta_content(text, "og:description")
                if description is None:
                    description = _extract_meta_content(text, "description")
                return description
            except Exception:
                return None

        return None
    except Exception:
        return None

# -------- GITHUB --------
def get_github_description(repo_slug):
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
        return data.get("description")
    except Exception:
        return None

# -------- PLATFORM DETECTION --------
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
    parser = argparse.ArgumentParser(description="Extract plugin description from Modrinth, SpigotMC, or Hangar URLs")
    parser.add_argument("url", nargs="?", help="Plugin URL from Modrinth, SpigotMC, or Hangar")
    args = parser.parse_args()

    if not args.url:
        args.url = input("Enter a plugin URL: ").strip()

    platform, identifier = detect_platform(args.url)
    if not platform:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if platform == "modrinth":
        description = get_modrinth_description(identifier)
    elif platform == "spigot":
        description = get_spigot_description(identifier)
    elif platform == "hangar":
        description = get_hangar_description(identifier)
    elif platform == "curseforge":
        description = get_curseforge_description(identifier)
    elif platform == "bukkitdev":
        description = get_bukkitdev_description(identifier)
    elif platform == "github":
        description = get_github_description(identifier)
    else:
        print("Invalid URL", file=sys.stderr)
        sys.exit(1)

    if description is None:
        print("", file=sys.stderr)
        sys.exit(1)
    else:
        print(description)

if __name__ == "__main__":
    main()
