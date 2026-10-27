import json
import time
import subprocess
import os
import sys
from datetime import datetime, timedelta
import requests
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "vulcanocraft")

def get_db():
    try:
        from webserver import db
        return db
    except Exception:
        client = MongoClient(MONGO_URI)
        return client[MONGO_DB_NAME]

def load_plugins():
    """Laad de plugins data"""
    try:
        db = get_db()
        plugins = list(db.plugins.find({}, {"_id": 0}))
        return plugins
    except Exception as e:
        print(f"Fout bij het laden van plugins: {e}")
        return []

def record_cron_status():
    """Sla de huidige datum/tijd op als last_fetched in settings"""
    try:
        db = get_db()
        now_iso = datetime.now().isoformat()
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
                pass

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

        is_version_changed = (old_v != new_v) and bool(new_v)

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
            if updated_data:
                detect_and_record_changes(existing, updated_data, owner)
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
    return success_count

def main():
    """Hoofdfunctie die elke 6 uur alle plugins bijwerkt"""
    print("Cron service gestart - Ctrl+C om te stoppen")
    print(f"Python executable: {sys.executable}")
    print("-" * 50)
    
    while True:
        try:
            run_cron_cycle()
            
            next_run = datetime.now() + timedelta(hours=6)
            print(f"Volgende update om: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 50)
            
            time.sleep(21600)
            
        except KeyboardInterrupt:
            print("\nCron service gestopt door gebruiker")
            break
        except Exception as e:
            print(f"Onverwachte fout in hoofdloop: {e}")
            time.sleep(300)

if __name__ == "__main__":
    main()
