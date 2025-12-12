import re
from urllib.parse import urlparse

def detect_platform(url):
    """Detects the platform and returns a platform identifier and a specific identifier from the URL."""
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()

        if "modrinth.com" in host:
            match = re.search(r"/(plugin|mod)/([^/]+)/?", parsed.path)
            if match:
                return "modrinth", match.group(2)

        elif "spigotmc.org" in host:
            match = re.search(r'/resources/[^/]+\.(\d+)/?', parsed.path)
            if match:
                return "spigot", match.group(1)

        elif "hangar.papermc.io" in host:
            match = re.search(r"/([^/]+)/([^/]+)/?$", parsed.path)
            if match:
                author, project = match.group(1), match.group(2)
                return "hangar", f"{author}/{project}"

        elif "curseforge.com" in host or "dev.bukkit.org" in host:
            # Treat dev.bukkit.org as curseforge
            match = re.search(r'/(projects|minecraft/bukkit-plugins)/([^/]+)', parsed.path)
            if match:
                return "curseforge", match.group(2)

        elif "github.com" in host:
            match = re.search(r"/([^/]+)/([^/]+)/?$", parsed.path)
            if match:
                owner, repo = match.group(1), match.group(2)
                return "github", f"{owner}/{repo}"

        return None, None
    except Exception:
        return None, None
