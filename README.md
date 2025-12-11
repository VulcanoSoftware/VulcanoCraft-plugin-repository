# VulcanoCraft Plugin Repository Tool

[![CodeFactor](https://www.codefactor.io/repository/github/vulcanosoftware/vulcanocraft-plugin-repository/badge)](https://www.codefactor.io/repository/github/vulcanosoftware/vulcanocraft-plugin-repository)

This repository contains a **Python-based tool** that automatically **fetches plugin information** and keeps it up to date.  
It includes a web interface for viewing the collected data, user management, and an admin panel.

---

## 🚀 Features
- 🐳 **Dockerized for Production** – Easy to deploy and manage with Docker Compose.
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

## 🐳 Production Setup with Docker

This application is designed to run in production using Docker and Docker Compose.

### Requirements
- Docker
- Docker Compose

### 1. Initial Setup

Before starting the containers, you need to create the necessary JSON files for data storage. These files will be mounted into the containers, ensuring your data is persisted on the host machine.

Create the following empty JSON files in the root of the repository:
- `plugins.json` (use `[]`)
- `users.json` (use `[]`)
- `server_categories.json` (use `[]`)
- `loaders.json` (use `[]`)
- `settings.json` (use `{}`)

```bash
touch plugins.json users.json server_categories.json loaders.json settings.json
echo "[]" > plugins.json
echo "[]" > users.json
echo "[]" > server_categories.json
echo "[]" > loaders.json
echo "{}" > settings.json
```

### 2. Build and Start the Services

Build and start the web application and the background cron job using Docker Compose:

```bash
docker-compose up --build -d
```
The web application will be accessible at `http://localhost:5000`.

### 3. Create an Admin Account

Once the `app` container is running, create the initial admin account by executing the `create_admin.py` script inside the container:

```bash
docker-compose exec app python create_admin.py
```
You will be prompted to enter a username and password for the new admin account.

### 4. Managing the Services

- **View Logs:**
  To see the logs for the web server or the cron job:
  ```bash
  # View logs for the web server
  docker-compose logs -f app

  # View logs for the cron job
  docker-compose logs -f cron
  ```

- **Stop Services:**
  To stop the running containers:
  ```bash
  docker-compose down
  ```

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
<p align="right">made possible by <code>_.g.a.u.t.a.m._</code> on discord.</p>
<p align="right">made possible by <code>Swapnanilb</code> on https://github.com/Swapnanilb</p>
<p align="right">made possible by <code>luxetidal</code> on https://github.com/luxetidal</p>
<p align="right">made possible by <code>AlexTrinityBlock</code> on https://github.com/AlexTrinityBlock</p>
