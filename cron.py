import time
import subprocess
import sys
from datetime import datetime, timedelta
from database import get_plugins_collection

def update_plugin(url):
    """
    Voert launcher.py uit voor een specifieke plugin URL met 'confirm',
    zodat de data direct in de database wordt opgeslagen.
    """
    try:
        print(f"Start bijwerken van plugin: {url}")
        
        # Gebruik de Python executable van de huidige omgeving
        python_executable = sys.executable
        
        # Roep launcher.py aan met 'confirm' om de data direct op te slaan
        result = subprocess.run(
            [python_executable, 'launcher.py', url, 'confirm'],
            capture_output=True,
            text=True,
            check=True,
            timeout=300  # 5 minuten timeout
        )
        
        # Toon de output van de launcher voor logging
        print(f"Output voor {url}: {result.stdout.strip()}")
        print(f"Plugin succesvol bijgewerkt: {url}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Fout bij bijwerken plugin {url}:", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print(f"Timeout bij bijwerken plugin {url}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Onverwachte fout bij bijwerken plugin {url}: {e}", file=sys.stderr)
        return False

def main():
    """Hoofdfunctie die periodiek alle plugins in de database bijwerkt."""
    print("Cron service gestart - Ctrl+C om te stoppen")
    print("-" * 50)
    
    while True:
        try:
            plugins_collection = get_plugins_collection()
            plugins_to_update = list(plugins_collection.find())
            
            if not plugins_to_update:
                print("Geen plugins gevonden in de database om bij te werken.")
            else:
                total_plugins = len(plugins_to_update)
                print(f"Start bijwerken van {total_plugins} plugin(s)...")
                
                success_count = 0
                for plugin in plugins_to_update:
                    url = plugin.get('url')
                    if url:
                        if update_plugin(url):
                            success_count += 1
                    else:
                        print("Plugin zonder URL gevonden, wordt overgeslagen.", file=sys.stderr)
                
                print(f"Bijwerken voltooid: {success_count}/{total_plugins} plugins succesvol bijgewerkt.")
            
            # Wacht 1 uur tot de volgende update cyclus
            next_run = datetime.now() + timedelta(hours=1)
            print("-" * 50)
            print(f"Volgende update cyclus start om: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            
            time.sleep(3600)  # Wacht 1 uur
            
        except KeyboardInterrupt:
            print("\nCron service gestopt door gebruiker.")
            break
        except Exception as e:
            print(f"Onverwachte fout in de hoofdloop van de cron service: {e}", file=sys.stderr)
            # Wacht 5 minuten voordat er opnieuw wordt geprobeerd na een serieuze fout
            time.sleep(300)

if __name__ == "__main__":
    main()
