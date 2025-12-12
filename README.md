# VulcanoCraft Plugin Repository Tool

[![CodeFactor](https://www.codefactor.io/repository/github/vulcanosoftware/vulcanocraft-plugin-repository/badge)](https://www.codefactor.io/repository/github/vulcanosoftware/vulcanocraft-plugin-repository)

This repository contains a **Python-based tool** that automatically **fetches plugin information** and keeps it up to date.  
It includes a modern web interface for browsing plugins and a Docker-first deployment with MongoDB, cron, and optional automated backups.

---

## 🚀 Features
- 🔄 **Automated Updates** – Background service fetches and updates plugin information hourly.
- 👥 **User Management** – Registration, login, and role-based permissions (User, Co-Admin, Admin).
- 🎨 **Modern UI** – Responsive design with animations and advanced filtering capabilities.
- 🔍 **Advanced Filtering** – Search by name, version, platform, or loader.
- 🛡️ **Admin Panel** – Manage users, plugins, categories, and system settings.
- ⚡ **Optimized Scraping** – Fast plugin data fetching with Playwright.
- 🖼️ **Smart Icons** – Automatic fallback to letter-based logos for broken images.
- 📂 **Category Management** – Create, rename, and delete server categories.
- 🔌 **Loader Filtering** – Filter plugins by their supported loaders (e.g., Paper, Spigot, Fabric).
- 📢 **Public API** – Public API endpoint to access all plugins without authentication.

---

## 📂 Repository Structure (overzicht)
```
├── webserver.py            # Flask web server met API endpoints
├── cron.py                 # Background updater (cron-achtige job)
├── launcher.py             # Lokale tool om plugin-data op te halen
├── create_admin.py         # CLI-tool om een admin-gebruiker aan te maken
├── docker-compose.yml      # Docker stack (app + mongo + cron + backup)
├── Dockerfile              # Image voor de app / cron
├── .env                    # Gevoelige configuratie (niet in git)
├── fetchers/               # Platform-specifieke scrapers (Spigot, Modrinth, CurseForge, ...)
│   ├── author.py
│   ├── description.py
│   ├── icon.py
│   ├── titles.py
│   ├── versions.py
│   └── loaders.py
├── components/
│   ├── admin/
│   │   └── admin.html      # Admin panel interface
│   └── user/
│       └── login.html      # Login/registratie
├── images/                 # UI-assets en iconen
├── js/                     # Moderne modular frontend (filters, UI, auth, modals)
├── index.html              # Hoofd plugin-browser interface
├── style.css               # Styling en animaties
├── requirements.txt        # Python dependencies
├── README.md               # Deze documentatie
├── update.md               # Changelog / update-log
├── ADMIN_CHANGES.md        # Historische beschrijving van admin-wijzigingen
└── ADMIN_ROLES.md          # Uitleg over rolensysteem
```

---

## 🛠️ Installatie & Gebruik

### 1. Vereisten
- Python 3.11
- `uv` (Python package manager) – voor lokale ontwikkeling
- Docker + Docker Compose – aanbevolen voor productie

---

### 2. Configuratie via `.env` (1 file voor alles)

In de root van het project staat een `.env` bestand dat **alle gevoelige waarden** bevat.  
Docker Compose leest deze automatisch in.

Een typisch `.env` voorbeeld:

```env
# MongoDB
MONGO_ROOT_USERNAME=vulcano_root
MONGO_ROOT_PASSWORD=een-sterk-wachtwoord
MONGO_DB_NAME=vulcanocraft
MONGO_URI=mongodb://vulcano_root:een-sterk-wachtwoord@mongo:27017/vulcanocraft?authSource=admin
MONGO_BACKUP_URI=mongodb://vulcano_root:een-sterk-wachtwoord@mongo:27017/vulcanocraft?authSource=admin

# Flask / applicatie
FLASK_SECRET_KEY=64-tekens-lange-random-hex-string
ADMIN_DEFAULT_PASSWORD=een-sterk-admin-wachtwoord

# CurseForge
CURSEFORGE_API_KEY=jouw-curseforge-api-key-hier

# Backups
ENABLE_BACKUPS=false
BACKUP_INTERVAL_HOURS=24
```

Belangrijk:
- Gebruik sterke wachtwoorden (geen `admin123` of `test`).
- Zorg dat `MONGO_URI` en `MONGO_BACKUP_URI` overeenkomen met `MONGO_ROOT_USERNAME` en `MONGO_ROOT_PASSWORD`.
- `FLASK_SECRET_KEY` moet lang en willekeurig zijn (64 hex-karakters is prima).

---

### 3. Lokaal draaien (zonder Docker)

Dit is vooral handig voor ontwikkeling of debugging.

1. Dependencies installeren:

```bash
uv pip install -r requirements.txt
```

2. Playwright browsers installeren (voor de fetchers):

```bash
playwright install
```

3. Omgevingsvariabelen zetten (powershell-voorbeeld):

```powershell
$env:MONGO_URI = "mongodb://localhost:27017"
$env:MONGO_DB_NAME = "vulcanocraft"
$env:FLASK_SECRET_KEY = "vervang-dit-met-een-veilige-sleutel"
```

4. MongoDB lokaal starten (bijvoorbeeld via Docker of een lokale installatie).

5. Webserver starten:

```bash
uv run webserver.py
```

Applicatie is dan bereikbaar op `http://localhost:5000`.

6. Cronjob (optioneel):

```bash
uv run cron.py
```

Deze job werkt bestaande plugins periodiek bij.

---

### 4. Draaien met Docker (aanbevolen voor productie)

Zorg dat Docker en Docker Compose geïnstalleerd zijn.

1. Zorg dat `.env` correct is ingevuld (zie hierboven).

2. Bouw en start alle services:
   ```bash
   docker compose up -d
   ```
   Dit start:
   - `app` – Flask-app achter een productie WSGI-server (`gunicorn`) op poort `8000`
   - `mongo` – MongoDB met een persistent Docker volume `mongo-data`
   - `cron` – Updater die regelmatig plugins bijwerkt
   - `backup` – Optionele backupservice (afhankelijk van `ENABLE_BACKUPS`)

3. Maak een admin-account in de container (eenmalig):
   ```bash
   docker compose exec app python create_admin.py
   ```

4. Open de webinterface:
   - Applicatie: `http://localhost:8000`

De data in MongoDB blijft behouden in het `mongo-data` volume, ook als je de containers opnieuw opstart.

---

### 5. Backups inschakelen en terugzetten

#### 5.1 Waar komen de backups terecht?

In Docker Compose is de `backup` service zo geconfigureerd dat alle dumps in een map in je projectroot terechtkomen:

```yaml
backup:
  ...
  volumes:
    - ./backups:/backups
```

Op de host (Windows) vind je ze hier:

```text
<project-root>\backups\<timestamp>\
```

Bijvoorbeeld:

```text
backups\
  20251212-235900\
  20251213-001500\
```

Elke map bevat een `mongodump` van je database op dat moment.

#### 5.2 Backups inschakelen

1. Zet in `.env`:

```env
ENABLE_BACKUPS=true
BACKUP_INTERVAL_HOURS=24    # of 6, 12, ...
MONGO_BACKUP_URI=mongodb://vulcano_root:een-sterk-wachtwoord@mongo:27017/vulcanocraft?authSource=admin
```

2. Herstart de stack:

```bash
docker compose down
docker compose up -d
```

3. De `backup`-container zal nu, elke `BACKUP_INTERVAL_HOURS`,:
   - Een timestamp genereren (`YYYYMMDD-HHMMSS`)
   - `mongodump` draaien naar `/backups/<timestamp>`
   - Backups ouder dan 7 dagen verwijderen

#### 5.3 Een backup terugzetten (restore)

Stel je wilt een backup met timestamp `20251212-235900` terugzetten.

1. Stop de app en cron (optioneel, maar veiligst):

```bash
docker compose stop app cron
```

2. Start een eenmalige `mongo`-container met dezelfde netwerk/URI en mount de backups:

```bash
docker compose run --rm \
  -v ./backups:/backups \
  mongo \
  mongorestore --uri="$MONGO_BACKUP_URI" /backups/20251212-235900
```

3. Start de app weer:

```bash
docker compose start app cron
```

Na de restore zie je in de webinterface weer de data uit die backup.

> Let op: een restore overschrijft de huidige database-inhoud. Maak eventueel eerst een nieuwe backup voordat je een oude terugzet.

---

## 👥 User Roles

- **User** – Add, view, and delete own plugins
- **Co-Admin** – Manage all plugins and view users
- **Admin** – Full access including user management and settings

Meer details over rollen en rechten vind je in `ADMIN_ROLES.md`.

---

## 🌐 Supported Platforms

- **SpigotMC** – `spigotmc.org/resources/*`
- **Modrinth** – `modrinth.com/plugin/*`
- **Hangar** – `hangar.papermc.io/*/*`
- **CurseForge** – `curseforge.com/minecraft/*`

---

## 📝 API Endpoints

- `GET /` – Main plugin browser
- `GET /login-page` – User login/registration
- `GET /admin` – Admin panel
- `GET /api/plugins` – Get plugins for the authenticated user
- `GET /api/plugins/public` – Get all plugins (public)
- `GET /api/server_categories` – Get all server categories
- `GET /api/loaders` – Get all loaders
- `POST /add_plugin` – Add a new plugin (authenticated)
- `POST /delete_plugin` – Delete a plugin (authenticated)
- `POST /login` – User login
- `POST /register` – User registration
- `POST /logout` – User logout
- `GET /auth-status` – Check authentication status
- `GET /registration-status` – Check if registration is enabled
- `GET /admin/users` – Get all users (admin)
- `DELETE /admin/users/<username>` – Delete a user (admin)
- `POST /admin/users/<username>/role` – Change a user's role (admin)
- `GET /admin/plugins` – Get all plugins (admin)
- `DELETE /admin/plugins/<path:url>` – Delete a plugin (admin)

---
<p align="right">made possible by <code>_.g.a.u.t.a.m._</code> on discord.</p>
<p align="right">made possible by <code>Swapnanilb</code> on https://github.com/Swapnanilb</p>
<p align="right">made possible by <code>luxetidal</code> on https://github.com/luxetidal</p>
<p align="right">made possible by <code>AlexTrinityBlock</code> on https://github.com/AlexTrinityBlock</p>
