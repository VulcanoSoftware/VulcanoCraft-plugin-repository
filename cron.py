import json
import time
import subprocess
import os
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "vulcanocraft")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB_NAME]

def load_plugins():
    """Laad de plugins data"""
    try:
        plugins = list(db.plugins.find({}, {"_id": 0}))
        return plugins
    except Exception as e:
        print(f"Fout bij het laden van plugins: {e}")
        return []

def update_plugin(url, owner=None):
    """Voer launcher.py uit voor een specifieke plugin URL"""
    try:
        print(f"Bijwerken plugin: {url}")
        
        python_executable = sys.executable
        
        # Voer launcher.py uit zonder confirm om alleen data op te halen
        result = subprocess.run(
            [python_executable, 'launcher.py', url],
            capture_output=True,
            text=True,
            check=True,
            timeout=300
        )
        
        # Parse de JSON output
        if not result.stdout.strip():
            print(f"Geen output ontvangen voor plugin {url}")
            return None
            
        plugin_data = json.loads(result.stdout)
        
        # Behoud owner informatie
        if owner:
            plugin_data['owner'] = owner
        
        print(f"Plugin succesvol bijgewerkt: {url}")
        return plugin_data
        
    except subprocess.CalledProcessError as e:
        print(f"Fout bij bijwerken plugin {url}:")
        print(f"Error output: {e.stderr}")
        return None
    except subprocess.TimeoutExpired:
        print(f"Timeout bij bijwerken plugin {url}")
        return None
    except json.JSONDecodeError as e:
        print(f"Ongeldige JSON output voor plugin {url}: {e}")
        print(f"Output was: {result.stdout[:200]}...")
        return None
    except Exception as e:
        print(f"Onverwachte fout bij bijwerken plugin {url}: {e}")
        return None

def save_plugins(plugins):
    """Sla plugins op"""
    try:
        if not isinstance(plugins, list):
            return False
        db.plugins.delete_many({})
        if plugins:
            db.plugins.insert_many(plugins)
        return True
    except Exception as e:
        print(f"Fout bij het opslaan van plugins: {e}")
        return False

def main():
    """Hoofdfunctie die elke 6 uur alle plugins bijwerkt"""
    print("Cron service gestart - Ctrl+C om te stoppen")
    print(f"Python executable: {sys.executable}")
    print("-" * 50)
    
    # Oneindige loop
    while True:
        try:
            plugins = load_plugins()

            if not plugins:
                print("Geen plugins gevonden om bij te werken")
            else:
                print(f"Start bijwerken van {len(plugins)} plugin(s)")
                
                success_count = 0

                for plugin in plugins:
                    url = plugin.get('url')
                    owner = plugin.get('owner')
                    
                    if url:
                        existing = db.plugins.find_one({"url": url, "owner": owner})
                        if not existing:
                            print(f"Plugin verwijderd tijdens update, overslaan: {url}")
                            continue

                        updated_data = update_plugin(url, owner)
                        if updated_data:
                            db.plugins.update_one(
                                {"url": url, "owner": owner},
                                {"$set": updated_data},
                                upsert=True,
                            )
                            success_count += 1
                        else:
                            print(f"Originele data behouden voor: {url}")
                            db.plugins.update_one(
                                {"url": url, "owner": owner},
                                {"$set": plugin},
                                upsert=True,
                            )
                    else:
                        print("Plugin zonder URL gevonden, overslaan...")
                
                print(f"Bijwerken voltooid: {success_count}/{len(plugins)} plugins succesvol bijgewerkt")
            
            # Wacht 6 uur tot volgende update
            next_run = datetime.now() + timedelta(hours=6)
            print(f"Volgende update om: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 50)
            
            # Wacht 6 uur (21600 seconden)
            time.sleep(21600)
            
        except KeyboardInterrupt:
            print("\nCron service gestopt door gebruiker")
            break
        except Exception as e:
            print(f"Onverwachte fout in hoofdloop: {e}")
            # Wacht 5 minuten voordat we opnieuw proberen bij een fout
            time.sleep(300)

if __name__ == "__main__":
    main()
