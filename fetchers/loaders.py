import requests
import sys
import json

def get_loaders(url):
    """Haalt de loaders voor een Modrinth-plugin op."""
    try:
        # Extract de project slug uit de URL
        slug = url.split('/')[-1] if url.endswith('/') else url.split('/')[-1]

        # Bouw de Modrinth API URL
        api_url = f"https://api.modrinth.com/v2/project/{slug}"

        # Maak de API-aanvraag
        response = requests.get(api_url)
        response.raise_for_status()  # Werpt een error als de statuscode geen 2xx is

        # Parse de JSON-respons
        project_data = response.json()

        # Haal de loaders op en formateer ze als een string
        loaders = project_data.get('loaders', [])
        return ' '.join(loaders)

    except requests.exceptions.RequestException as e:
        # Handel API-fouten af
        print(f"Error fetching data from Modrinth API: {e}", file=sys.stderr)
        return ""
    except json.JSONDecodeError:
        # Handel JSON-decodeerfouten af
        print(f"Error decoding JSON from Modrinth API for slug: {slug}", file=sys.stderr)
        return ""
    except Exception as e:
        # Handel andere onverwachte fouten af
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return ""

if __name__ == "__main__":
    if len(sys.argv) > 1:
        plugin_url = sys.argv[1]
        loaders = get_loaders(plugin_url)
        print(loaders)
