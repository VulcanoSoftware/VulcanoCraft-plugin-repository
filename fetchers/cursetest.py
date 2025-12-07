import requests
import re

API_KEY = "$2a$10$5387XaA52Y2G2D3LBnfK2eDKAoS86NJofRTwm8hgLPnZbqHXQ8KQC"

def extract_slug_from_url(url):
    """Haal de exacte slug uit de URL."""
    patterns = [
        r"mc-mods/([^/]+)",
        r"modpacks/([^/]+)", 
        r"texture-packs/([^/]+)",
        r"worlds/([^/]+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_mod_by_slug(slug):
    """Zoek mod via exacte slug."""
    headers = {
        'Accept': 'application/json',
        'x-api-key': API_KEY
    }
    
    # Eerst zoeken op slug
    url = "https://api.curseforge.com/v1/mods/search"
    params = {
        'gameId': 432,
        'slug': slug,
        'pageSize': 1
    }
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if data.get('data'):
        return data['data'][0]
    
    # Als niet gevonden via slug, probeer dan reguliere zoekopdracht
    params = {
        'gameId': 432,
        'searchFilter': slug.replace("-", " "),
        'pageSize': 10
    }
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if not data.get('data'):
        return None
    
    # Probeer exacte match te vinden
    for mod in data['data']:
        if mod.get('slug') and mod['slug'].lower() == slug.lower():
            return mod
        if mod.get('name') and mod['name'].lower().replace(" ", "-") == slug.lower():
            return mod
    
    # Als geen exacte match, toon opties
    return data['data']

def get_mod_files(mod_id):
    headers = {
        'Accept': 'application/json',
        'x-api-key': API_KEY
    }
    
    url = f"https://api.curseforge.com/v1/mods/{mod_id}/files"
    params = {'pageSize': 50}
    
    response = requests.get(url, headers=headers, params=params)
    return response.json().get('data', [])

def main():
    print("=== Minecraft Mod/Plugin Modloader Finder ===")
    user_input = input("Voer de naam of CurseForge link van de mod in: ").strip()

    if not user_input:
        print("❌ Geen invoer gegeven.")
        return

    # Controleer of het een URL is
    if "curseforge.com" in user_input.lower():
        slug = extract_slug_from_url(user_input)
        if not slug:
            print("❌ Kon geen slug uit URL halen.")
            return
        print(f"🔍 Zoeken op slug: {slug}")
        result = get_mod_by_slug(slug)
    else:
        # Zoek op naam
        print(f"🔍 Zoeken op naam: {user_input}")
        result = get_mod_by_slug(user_input)

    if not result:
        print("❌ Geen resultaten gevonden.")
        return

    # Als result een lijst is, toon keuzes
    if isinstance(result, list):
        print("\n✅ Meerdere mods gevonden. Kies een optie:")
        for i, mod in enumerate(result[:10], 1):
            print(f"{i}. {mod['name']} (slug: {mod.get('slug', 'onbekend')})")
        
        try:
            choice = int(input("\nKies een nummer: ")) - 1
            if 0 <= choice < len(result):
                selected_mod = result[choice]
            else:
                print("❌ Ongeldige keuze.")
                return
        except (ValueError, IndexError):
            print("❌ Ongeldige invoer.")
            return
    else:
        # Exacte match gevonden
        selected_mod = result
        print(f"\n✅ Exacte match gevonden: {selected_mod['name']}")

    print(f"\n📦 Gekozen mod: {selected_mod['name']}")
    print(f"📎 Mod ID: {selected_mod['id']}")
    print(f"🔗 Slug: {selected_mod.get('slug', 'onbekend')}")

    files = get_mod_files(selected_mod['id'])
    
    if not files:
        print("❌ Geen bestanden gevonden voor deze mod.")
        return

    modloaders = set()
    game_versions = set()

    for file in files:
        if 'gameVersions' in file:
            for version in file['gameVersions']:
                v = version.lower()
                game_versions.add(v)
                
                if "forge" in v:
                    modloaders.add("Forge")
                elif "fabric" in v:
                    modloaders.add("Fabric")
                elif "quilt" in v:
                    modloaders.add("Quilt")
                elif "neoforge" in v:
                    modloaders.add("NeoForge")
                elif "rift" in v:
                    modloaders.add("Rift")
                elif "liteloader" in v:
                    modloaders.add("LiteLoader")

    # Toon Minecraft versies (optioneel)
    if game_versions:
        mc_versions = [v for v in game_versions if not any(loader in v for loader in ["forge", "fabric", "quilt", "neoforge", "rift", "liteloader"])]
        if mc_versions:
            print(f"\n🎮 Minecraft versies: {', '.join(sorted(mc_versions)[:5])}" + ("..." if len(mc_versions) > 5 else ""))

    if not modloaders:
        print("⚠️ Geen specifieke modloaders gevonden (mogelijk client-side of wereld/modpack).")
    else:
        print("\n✅ Ondersteunde modloaders:")
        for loader in sorted(modloaders):
            print(f"- {loader}")

if __name__ == "__main__":
    main()
