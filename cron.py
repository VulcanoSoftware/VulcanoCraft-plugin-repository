import json
import time
import subprocess
import os
import sys
from datetime import datetime, timedelta, timezone
import requests
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "vulcanocraft")

# Velden die door launcher.py/fetchers worden opgehaald. Een mislukte fetch levert
# voor deze velden een lege waarde op ("" of []), die nooit een gevulde waarde in de
# database mag overschrijven.
FETCHED_FIELDS = ("title", "description", "author", "icon", "versions", "loaders")

def _env_float(name, default):
    try:
        return max(0.0, float(os.getenv(name, default)))
    except (TypeError, ValueError):
        return float(default)

# Korte pauze tussen plugins, zodat een cyclus met honderden plugins de
# externe API's (Modrinth, GitHub, Spiget, ...) niet in één burst raakt.
PLUGIN_DELAY_SECONDS = _env_float("CRON_PLUGIN_DELAY", 1.0)

_db = None

def get_db():
    """Geef een gedeelde database-verbinding terug.

    Er wordt bewust niet uit webserver geïmporteerd: dat vereist o.a.
    FLASK_SECRET_KEY (niet beschikbaar in de cron-container) en voert
    migraties uit bij elke import.
    """
    global _db
    if _db is None:
        _db = MongoClient(MONGO_URI)[MONGO_DB_NAME]
    return _db

def load_plugins():
    """Laad de plugins data"""
    try:
        db = get_db()
        plugins = list(db.plugins.find({}, {"_id": 0}))
        return plugins
    except Exception as e:
        print(f"Fout bij het laden van plugins: {e}")
        return []

def _is_empty(value):
    """True voor None, lege/whitespace-strings en lege collecties."""
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False

def has_fetched_data(fetched):
    """True als minstens één opgehaald veld daadwerkelijk een waarde bevat."""
    return any(not _is_empty(fetched.get(field)) for field in FETCHED_FIELDS)

def merge_plugin_data(existing, fetched):
    """Combineer nieuw opgehaalde data met de bestaande plugin.

    Een leeg resultaat voor een veld (bijv. door rate limiting of een tijdelijke
    storing) overschrijft nooit een eerder opgeslagen, gevulde waarde. Zo kan één
    slechte cyclus de titels, auteurs, versies en loaders niet meer wissen.
    """
    merged = dict(fetched)
    for field in FETCHED_FIELDS:
        if _is_empty(merged.get(field)) and not _is_empty(existing.get(field)):
            merged[field] = existing[field]
    return merged

def record_cron_status():
    """Sla de huidige datum/tijd op als last_fetched in settings"""
    try:
        db = get_db()
        now_iso = datetime.now(timezone.utc).isoformat()
        db.settings.update_one(
            {"_id": "cron_status"},
            {"$set": {"last_fetched": now_iso}},
            upsert=True
        )
        print(f"Cron status bijgewerkt: {now_iso}")
    except Exception as e:
        print(f"Fout bij het opslaan van cron status: {e}")

def purge_old_records():
    """Verwijder notificaties en wijzigingshistorie ouder dan de retentieperiode"""
    try:
        db = get_db()
        doc = db.settings.find_one({"_id": "app_settings"}) or {}
        retention_days = doc.get("retention_days", 30)
        try:
            retention_days = int(retention_days)
        except (ValueError, TypeError):
            retention_days = 30

        if retention_days > 0:
            cutoff = datetime.now() - timedelta(days=retention_days)
            res_notif = db.notifications.delete_many({"created_at": {"$lt": cutoff}})
            res_changes = db.plugin_changes.delete_many({"created_at": {"$lt": cutoff}})
            print(f"Opschonen voltooid ({retention_days} dagen retentie): {res_notif.deleted_count} notificaties, {res_changes.deleted_count} wijzigingen verwijderd.")
    except Exception as e:
        print(f"Fout bij opschonen oude records: {e}")

def dispatch_discord_webhooks(title, message, url=None, old_version=None, new_version=None, owner=None):
    """Verstuur een notificatie naar de geconfigureerde Discord webhooks van ingelogde gebruikers"""
    try:
        db = get_db()
        users = list(db.users.find({
            "discord_notifications_enabled": True,
            "discord_webhook_url": {"$exists": True, "$ne": ""}
        }))

        if not users:
            return

        embed = {
            "title": f"🔔 {title}",
            "description": message,
            "color": 3066993,
            "timestamp": datetime.now().isoformat(),
            "fields": []
        }

        if url:
            embed["fields"].append({"name": "Plugin URL", "value": url, "inline": False})
        if old_version:
            embed["fields"].append({"name": "Oude Versie", "value": str(old_version), "inline": True})
        if new_version:
            embed["fields"].append({"name": "Nieuwe Versie", "value": str(new_version), "inline": True})

        payload = {
            "content": "New plugin update notification",
            "embeds": [embed]
        }

        for user in users:
            webhook_url = user.get("discord_webhook_url", "").strip()
            if not webhook_url:
                continue

            u_name = user.get("username")
            if owner and u_name and owner != u_name:
                continue

            try:
                res = requests.post(webhook_url, json=payload, timeout=5)
                if res.status_code in [200, 204]:
                    print(f"Discord webhook verzonden naar gebruiker {u_name}")
                else:
                    print(f"Discord webhook fout voor {u_name}: status {res.status_code}")
            except Exception as w_err:
                print(f"Fout bij versturen Discord webhook naar {u_name}: {w_err}")
    except Exception as e:
        print(f"Fout bij verwerken Discord webhooks: {e}")

def detect_and_record_changes(existing, updated_data, owner):
    """Vergelijk bestaande plugin met bijgewerkte data en sla notificaties + wijzigingshistorie op"""
    try:
        db = get_db()
        url = updated_data.get("url") or existing.get("url")
        title = updated_data.get("title") or existing.get("title") or "Onbekende Plugin"

        old_v = existing.get("latest_version") or existing.get("versions") or ""
        new_v = updated_data.get("latest_version") or updated_data.get("versions") or ""

        if isinstance(old_v, list):
            old_v = " ".join(old_v)
        if isinstance(new_v, list):
            new_v = " ".join(new_v)

        # Alleen een echte wijziging melden: als er nog geen vorige versie bekend was
        # (bijv. na een mislukte eerdere fetch) is dit een eerste vulling, geen update.
        is_version_changed = (old_v != new_v) and bool(new_v) and bool(old_v)

        if is_version_changed:
            msg = f"Nieuwe versie gedetecteerd voor '{title}': {new_v}"
            now_dt = datetime.now()
            now_iso = now_dt.isoformat()

            notif_doc = {
                "url": url,
                "plugin_title": title,
                "type": "version_update",
                "message": msg,
                "old_version": str(old_v),
                "new_version": str(new_v),
                "timestamp": now_iso,
                "created_at": now_dt,
                "owner": owner,
                "read": False
            }
            db.notifications.insert_one(notif_doc)

            change_doc = {
                "url": url,
                "plugin_title": title,
                "owner": owner,
                "category": updated_data.get("category") or existing.get("category") or "",
                "action": "version_update",
                "details": f"Versie bijgewerkt van '{old_v}' naar '{new_v}'",
                "old_version": str(old_v),
                "new_version": str(new_v),
                "timestamp": now_iso,
                "created_at": now_dt,
                "date": now_dt.strftime("%Y-%m-%d")
            }
            db.plugin_changes.insert_one(change_doc)

            print(f"Notificatie en wijziging opgeslagen voor {title}: {old_v} -> {new_v}")
            dispatch_discord_webhooks("Plugin Update Gedetecteerd", msg, url=url, old_version=old_v, new_version=new_v, owner=owner)

    except Exception as e:
        print(f"Fout bij vergelijken/opslaan van plugin wijzigingen: {e}")

def update_plugin(url, owner=None):
    """Voer launcher.py uit voor een specifieke plugin URL"""
    try:
        print(f"Bijwerken plugin: {url}")
        
        python_executable = sys.executable
        
        result = subprocess.run(
            [python_executable, 'launcher.py', url],
            capture_output=True,
            text=True,
            check=True,
            timeout=300
        )
        
        if not result.stdout.strip():
            print(f"Geen output ontvangen voor plugin {url}")
            return None
            
        plugin_data = json.loads(result.stdout)
        
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
        db = get_db()
        if not isinstance(plugins, list):
            return False
        db.plugins.delete_many({})
        if plugins:
            db.plugins.insert_many(plugins)
        return True
    except Exception as e:
        print(f"Fout bij het opslaan van plugins: {e}")
        return False

def run_cron_cycle():
    """Voer één update-cyclus van de cron-dienst uit"""
    db = get_db()
    record_cron_status()
    purge_old_records()

    plugins = load_plugins()

    if not plugins:
        print("Geen plugins gevonden om bij te werken")
        record_cron_status()
        return 0

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
            if updated_data and has_fetched_data(updated_data):
                merged_data = merge_plugin_data(existing, updated_data)
                detect_and_record_changes(existing, merged_data, owner)
                db.plugins.update_one(
                    {"url": url, "owner": owner},
                    {"$set": merged_data},
                    upsert=True,
                )
                success_count += 1
            else:
                # Ook als launcher.py "slaagt" maar overal een lege waarde teruggeeft
                # (alle fetchers mislukt), blijft de bestaande data ongemoeid. Er wordt
                # bewust niets teruggeschreven: de database bevat de data al, en een
                # momentopname van het begin van de cyclus zou wijzigingen van
                # gebruikers (bijv. een vastgepinde versie) kunnen terugdraaien.
                print(f"Originele data behouden voor: {url}")

            if PLUGIN_DELAY_SECONDS > 0:
                time.sleep(PLUGIN_DELAY_SECONDS)
        else:
            print("Plugin zonder URL gevonden, overslaan...")

    print(f"Bijwerken voltooid: {success_count}/{len(plugins)} plugins succesvol bijgewerkt")
    # Werk de timestamp ook na afloop bij, zodat "laatste cron fetch" de
    # afronding van de cyclus weergeeft.
    record_cron_status()
    return success_count

CODE_WATCH_DIRS = (".", "fetchers")

def _code_snapshot():
    """Map van .py-bestanden naar mtime, om codewijzigingen (updates) te detecteren."""
    snap = {}
    base = os.path.dirname(os.path.abspath(__file__))
    for d in CODE_WATCH_DIRS:
        folder = os.path.join(base, d)
        try:
            for name in os.listdir(folder):
                if name.endswith(".py"):
                    path = os.path.join(folder, name)
                    try:
                        snap[path] = os.stat(path).st_mtime
                    except OSError:
                        pass
        except OSError:
            pass
    return snap

def sleep_until_next_cycle(seconds, snapshot):
    """Slaap tot de volgende cyclus; stop het proces als de code is gewijzigd.

    De container herstart automatisch (restart: unless-stopped) met de nieuwe code.
    """
    waited = 0
    while waited < seconds:
        time.sleep(60)
        waited += 60
        if _code_snapshot() != snapshot:
            print("Codewijziging gedetecteerd, cron service stopt zodat Docker hem met de nieuwe code herstart...")
            sys.stdout.flush()
            sys.exit(0)

def main():
    """Hoofdfunctie die elke 6 uur alle plugins bijwerkt"""
    print("Cron service gestart - Ctrl+C om te stoppen")
    print(f"Python executable: {sys.executable}")
    print("-" * 50)
    
    while True:
        try:
            snapshot = _code_snapshot()
            run_cron_cycle()
            
            next_run = datetime.now() + timedelta(hours=6)
            print(f"Volgende update om: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 50)
            
            sleep_until_next_cycle(21600, snapshot)
            
        except KeyboardInterrupt:
            print("\nCron service gestopt door gebruiker")
            break
        except Exception as e:
            print(f"Onverwachte fout in hoofdloop: {e}")
            time.sleep(300)

if __name__ == "__main__":
    main()
