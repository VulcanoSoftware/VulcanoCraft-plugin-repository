import requests
import json
import sys

def search_for_projects(query, filters=None):
    """
    Searches for projects on Modrinth with a given query and filters.
    """
    base_url = "https://api.modrinth.com/v2/search"

    params = {}
    if query:
        params['query'] = query

    facets = []
    if filters:
        for key, value in filters.items():
            if value:
                facets.append(f'["{key}:{value}"]')

    if facets:
        params['facets'] = f"[{','.join(facets)}]"

    headers = {
        "User-Agent": "Modrinth Fetcher"
    }

    response = requests.get(base_url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python modrinth.py <query> [filters]")
        sys.exit(1)

    query = sys.argv[1]
    filters_json = sys.argv[2] if len(sys.argv) > 2 else None

    filters = {}
    if filters_json:
        try:
            filters = json.loads(filters_json)
        except json.JSONDecodeError:
            print("Error: Invalid JSON format for filters.", file=sys.stderr)
            sys.exit(1)

    try:
        results = search_for_projects(query, filters)
        print(json.dumps(results, indent=4))
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Modrinth: {e}", file=sys.stderr)
        sys.exit(1)
