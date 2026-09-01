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
git clone https://github.com/VulcanoSoftware/VulcanoCraft-plugin-repository.git
```

```bash
cd VulcanoCraft-plugin-repository
```

```bash
docker-compose build app && docker-compose up -d
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
    vulcanocraft/
  20251213-001500/
    vulcanocraft/
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

2. Restore the backup from the timestamp directory for your database:

```bash
docker compose run --rm \
  -v ./backups:/backups \
  mongo \
  sh -c 'mongorestore \
    --host mongo \
    --port 27017 \
    -u "$MONGO_INITDB_ROOT_USERNAME" \
    -p "$MONGO_INITDB_ROOT_PASSWORD" \
    --authenticationDatabase admin \
    --db "$MONGO_INITDB_DATABASE" \
    --drop \
    /backups/20251212-235900/vulcanocraft'
```

3. Start the app and cron again:

```bash
docker compose start app cron
```

After the restore, you will see the data from that backup again in the web interface.

> Note: a restore overwrites the current database content. Consider creating a new backup first before restoring an older one.
>
---
>
### 6. Running on ARM64 / Raspberry Pi 4
>
The application is written in pure Python and uses Docker images that are available as multi-architecture builds. That means it can run on any 64-bit CPU, including ARM64 platforms such as a Raspberry Pi 4, as long as you use a 64-bit operating system.
>
To run on a Raspberry Pi 4 (or another ARM64 server) with Docker:
>
- Use a 64-bit OS (for example Raspberry Pi OS 64-bit or Ubuntu Server 64-bit).
- Install Docker and Docker Compose in the standard way for your distribution.
- Clone this repository and create a `.env` file as described above.
- Start the stack in exactly the same way:
  - `docker compose build app`
  - `docker compose up -d`
>
Docker will automatically pull the correct `python:3.11-slim` and `mongo:4.4` images for your CPU architecture (including `linux/arm64`). No extra configuration is required.
>
If you prefer to run the app without Docker on ARM64:
>
- Install Python 3.11 for your platform.
- Install the dependencies with `uv pip install -r requirements.txt` or `pip install -r requirements.txt`.
- Run `playwright install` once to install the browser binaries. On ARM64 this automatically downloads the correct Playwright build for your CPU.
- Set `MONGO_URI`, `MONGO_DB_NAME` and `FLASK_SECRET_KEY` as environment variables.
- Start the web server with `uv run webserver.py` or `python webserver.py`.
>
If you run into architecture-related issues (for example browser installation errors on very minimal ARM distributions), you can still use the tool because the core fetchers primarily rely on HTTP requests. In that case:
>
- Make sure Python and `requests` are installed.
- Ensure MongoDB is reachable via `MONGO_URI`.
- Skip Playwright-based optimizations if the browser installation is not available on your platform.
>
On Raspberry Pi 4 specifically, the CPU is ARMv8.0-A. Recent official MongoDB builds for arm64 (including `mongo:4.4` tags ≥4.4.19) require ARMv8.2-A or newer and will crash with `Illegal instruction` on a Pi 4. For this reason, the Docker configuration in this repository pins MongoDB to `mongo:4.4.18`, which is the latest 4.4 release that still runs reliably on Raspberry Pi 4 according to the upstream issue tracker.
>
---
>
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
