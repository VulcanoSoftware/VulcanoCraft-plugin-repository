# VulcanoCraft Plugin Repository Tool

[![CodeFactor](https://www.codefactor.io/repository/github/vulcanosoftware/vulcanocraft-plugin-repository/badge)](https://www.codefactor.io/repository/github/vulcanosoftware/vulcanocraft-plugin-repository)

This repository contains a **Python-based tool** that automatically **fetches plugin information** and keeps it up to date.  
It includes a small web interface for viewing the collected data, but its main focus is background automation.

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

## 📂 Repository Structure
```
├── cron.py                 # Background updater (hourly plugin updates)
├── webserver.py            # Flask web server with API endpoints
├── launcher.py             # Plugin data fetcher
├── create_admin.py         # Admin account creation utility
├── fetchers/               # Platform-specific data scrapers
│   ├── author.py
│   ├── description.py
│   ├── icon.py
│   ├── titles.py
│   └── versions.py
├── components/
│   ├── admin/
│   │   └── admin.html      # Admin panel interface
│   └── user/
│       └── login.html      # User login/registration page
├── images/                 # UI assets and icons
├── index.html              # Main plugin browser interface
├── style.css               # Styling and animations
├── plugins.json            # Plugin database
├── users.json              # User accounts database
├── server_categories.json  # Server categories
├── loaders.json            # Loader data
└── requirements.txt        # Python dependencies
```

---

## 🛠️ Installation & Usage

### Requirements
- Python 3.11
- uv (Python package manager)

### Setup
```bash
# Install dependencies
uv pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Create admin account
python create_admin.py
```

### Running the Application

**Start the web server:**
```bash
uv run webserver.py
```
Access at: `http://localhost:5000`

**Start background updater (optional):**
```bash
uv run cron.py
```
Updates all plugins every hour automatically.

---

## 👥 User Roles

- **User** – Add, view, and delete own plugins
- **Co-Admin** – Manage all plugins and view users
- **Admin** – Full access including user management and settings

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
