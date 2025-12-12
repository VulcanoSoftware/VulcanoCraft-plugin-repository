# VulcanoCraft Plugin Repository Tool

[![CodeFactor](https://www.codefactor.io/repository/github/vulcanosoftware/vulcanocraft-plugin-repository/badge)](https://www.codefactor.io/repository/github/vulcanosoftware/vulcanocraft-plugin-repository)

This repository contains a **Python-based tool** that automatically **fetches plugin information** and keeps it up to date.  
It includes a modern web interface for browsing plugins and a Docker-first deployment with MongoDB, cron, and optional automated backups.

---

## 🚀 Features
- 🔄 **Automated Updates** – Background service that fetches and updates plugin information hourly.
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

## 📂 Repository Structure (overview)
```
├── webserver.py            # Flask web server with API endpoints
├── cron.py                 # Background updater (cron-like job)
├── launcher.py             # Local tool to fetch plugin data
├── create_admin.py         # CLI tool to create an admin user
├── docker-compose.yml      # Docker stack (app + mongo + cron + backup)
├── Dockerfile              # Image for the app / cron
├── .env                    # Sensitive configuration (not in git)
├── fetchers/               # Platform-specific scrapers (Spigot, Modrinth, CurseForge, ...)
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
│       └── login.html      # Login/registration
├── images/                 # UI assets and icons
├── js/                     # Modern modular frontend (filters, UI, auth, modals)
├── index.html              # Main plugin browser interface
├── style.css               # Styling and animations
├── requirements.txt        # Python dependencies
├── README.md               # This documentation
├── update.md               # Changelog / update log
├── ADMIN_CHANGES.md        # Historical description of admin changes
└── ADMIN_ROLES.md          # Explanation of the role system
```

---

## 🛠️ Installation & Usage

### 1. Requirements
- Python 3.11
- `uv` (Python package manager) – recommended for local development
- Docker + Docker Compose – recommended for production

---

### 2. Configuration via `.env` (single config file)

In the project root there is a `.env` file that contains **all sensitive values**.  
Docker Compose automatically loads this file.

A typical `.env` example:

```env
# MongoDB
MONGO_ROOT_USERNAME=vulcano_root
MONGO_ROOT_PASSWORD=a-strong-password
MONGO_DB_NAME=vulcanocraft
MONGO_URI=mongodb://vulcano_root:a-strong-password@mongo:27017/vulcanocraft?authSource=admin
MONGO_BACKUP_URI=mongodb://vulcano_root:a-strong-password@mongo:27017/vulcanocraft?authSource=admin

# Flask / application
FLASK_SECRET_KEY=64-character-long-random-hex-string
ADMIN_DEFAULT_PASSWORD=a-strong-admin-password

# CurseForge
CURSEFORGE_API_KEY=your-curseforge-api-key-here

# Backups
ENABLE_BACKUPS=false
BACKUP_INTERVAL_HOURS=24
```

Important:
- Use strong passwords (do not use `admin123` or `test`).
- Ensure that `MONGO_URI` and `MONGO_BACKUP_URI` match `MONGO_ROOT_USERNAME` and `MONGO_ROOT_PASSWORD`.
- `FLASK_SECRET_KEY` must be long and random (64 hex characters is fine).

---

### 3. Running locally (without Docker)

This is mainly useful for development or debugging.

1. Install dependencies:

```bash
uv pip install -r requirements.txt
```

2. Install Playwright browsers (for the fetchers):

```bash
playwright install
```

3. Set environment variables

Windows PowerShell example:

```powershell
$env:MONGO_URI = "mongodb://localhost:27017"
$env:MONGO_DB_NAME = "vulcanocraft"
$env:FLASK_SECRET_KEY = "replace-this-with-a-secure-key"
```

Linux/macOS (bash/zsh) example:

```bash
export MONGO_URI="mongodb://localhost:27017"
export MONGO_DB_NAME="vulcanocraft"
export FLASK_SECRET_KEY="replace-this-with-a-secure-key"
```

4. Start MongoDB locally (for example via Docker or a local installation).

5. Start the web server:

```bash
uv run webserver.py
```

The application is then available at `http://localhost:5000`.

6. Cron job (optional):

```bash
uv run cron.py
```

This job periodically updates existing plugins.

---

### 4. Running with Docker (recommended for production)

Make sure Docker and Docker Compose are installed.

1. Make sure `.env` is filled in correctly (see above).

2. Build and start all services:

```bash
docker compose up -d
```

This starts:
- `app` – Flask app behind a production WSGI server (`gunicorn`) on port `8000`
- `mongo` – MongoDB with persistent data in `./mongo-live-data` in the project root
- `cron` – Updater that regularly refreshes plugins
- `backup` – Optional backup service (depending on `ENABLE_BACKUPS`)

3. Create an admin account inside the container (one-time):

```bash
docker compose exec app python create_admin.py
```

4. Open the web interface:
- Application: `http://localhost:8000`

MongoDB data is persisted in the `mongo-live-data` directory in your project root, even if you restart the containers.

---

### 5. Enabling and restoring backups

#### 5.1 Where are backups stored?

In Docker Compose, the `backup` service is configured so that all dumps end up in a directory in your project root:

```yaml
backup:
  ...
  volumes:
    - ./backups:/backups
```

On the host you will find them here:

```text
<project-root>/backups/<timestamp>/
```

For example:

```text
backups/
  20251212-235900/
  20251213-001500/
```

Each directory contains a `mongodump` of your database at that moment.

#### 5.2 Enabling backups

1. In `.env` set:

```env
ENABLE_BACKUPS=true
BACKUP_INTERVAL_HOURS=24    # or 6, 12, ...
MONGO_BACKUP_URI=mongodb://vulcano_root:a-strong-password@mongo:27017/vulcanocraft?authSource=admin
```

2. Restart the stack:

```bash
docker compose down
docker compose up -d
```

3. The `backup` container will now, every `BACKUP_INTERVAL_HOURS`:
- Generate a timestamp (`YYYYMMDD-HHMMSS`)
- Run `mongodump` to `/backups/<timestamp>`
- Delete backups older than 7 days

#### 5.3 Restoring a backup

Assume you want to restore a backup with timestamp `20251212-235900`.

1. Stop the app and cron (optional, but safest):

```bash
docker compose stop app cron
```

2. Start a one-off `mongo` container with the same network/URI and mount the backups:

```bash
docker compose run --rm \
  -v ./backups:/backups \
  mongo \
  mongorestore --uri="$MONGO_BACKUP_URI" /backups/20251212-235900
```

3. Start the app again:

```bash
docker compose start app cron
```

After the restore, you will see the data from that backup again in the web interface.

> Note: a restore overwrites the current database content. Consider creating a new backup first before restoring an older one.

---

## 👥 User Roles

- **User** – Add, view, and delete own plugins
- **Co-Admin** – Manage all plugins and view users
- **Admin** – Full access including user management and settings

More details about roles and permissions can be found in `ADMIN_ROLES.md`.

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
