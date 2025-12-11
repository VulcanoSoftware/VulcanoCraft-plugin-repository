import re
from urllib.parse import urlparse

def detect_platform(url):
    """Detecteert het platform en de identifier van een URL."""
    try:
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        path = parsed_url.path

        if "modrinth.com" in host:
            match = re.search(r"/(plugin|mod)/([^/]+)", path)
            if match:
                return "modrinth", match.group(2)

        elif "spigotmc.org" in host:
            return "spigot", url

        elif "hangar.papermc.io" in host:
            match = re.search(r"/([^/]+)/([^/]+)", path)
            if match:
                return "hangar", f"{match.group(1)}/{match.group(2)}"

        elif "curseforge.com" in host or "dev.bukkit.org" in host:
            # Behandel dev.bukkit.org als curseforge
            if "dev.bukkit.org" in host:
                # Converteer dev.bukkit.org URL naar een slug die gebruikt kan worden met de CurseForge API
                # Bv: https://dev.bukkit.org/projects/uberenchant -> uberenchant
                match = re.search(r'/projects/([^/]+)', path)
                if match:
                    return "curseforge", match.group(1)
            else:
                # Standaard CurseForge URL
                match = re.search(r'/(?:minecraft/)?([^/]+)/([^/]+)', path)
                if match:
                    return "curseforge", match.group(2)

        elif "github.com" in host:
            match = re.search(r"/([^/]+)/([^/]+)", path)
            if match:
                repo_identifier = f"{match.group(1)}/{match.group(2)}"
                # Verwijder een eventuele .git extensie
                if repo_identifier.endswith('.git'):
                    repo_identifier = repo_identifier[:-4]
                return "github", repo_identifier

        return None, None
    except Exception:
        return None, None
