import requests
import json

def fetch_loaders():
    """Fetch a list of loaders from the Modrinth API and save them to a file."""
    try:
        response = requests.get("https://api.modrinth.com/v2/tag/loader")
        response.raise_for_status()
        loaders = response.json()

        # Filter for loaders that support mods or modpacks
        supported_loaders = [
            loader for loader in loaders
            if "mod" in loader["supported_project_types"] or "modpack" in loader["supported_project_types"]
        ]

        with open("loaders.json", "w", encoding="utf-8") as f:
            json.dump(supported_loaders, f, indent=4)

        print(f"Successfully fetched and saved {len(supported_loaders)} loaders.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Modrinth API: {e}")
    except IOError as e:
        print(f"Error writing to loaders.json: {e}")

if __name__ == "__main__":
    fetch_loaders()
