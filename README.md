# VulcanoCraft Plugin Repository Tool

[![CodeFactor](https://www.codefactor.io/repository/github/vulcanosoftware/vulcanocraft-plugin-repository/badge)](https://www.codefactor.io/repository/github/vulcanosoftware/vulcanocraft-plugin-repository)

Dit project biedt een **volledig gecontaineriseerde, self-hosted webapplicatie** voor het beheren en weergeven van een verzameling Minecraft-plugins. Het haalt automatisch plugin-informatie op van diverse platforms en biedt een moderne webinterface met geavanceerde filteropties.

Dankzij Docker is de installatie en het beheer sterk vereenvoudigd en is de applicatie klaar voor productie.

---

## 🚀 Kenmerken

- 🐳 **Volledig Gecontaineriseerd** – Eenvoudige installatie en beheer met Docker en Docker Compose.
- 🔒 **Productie-Klaar** – Maakt gebruik van een Gunicorn WSGI-server voor robuuste prestaties.
- 💾 **Persistente Data** – Alle data (plugins, gebruikers, etc.) wordt opgeslagen in een MongoDB-database met een persistent volume.
- 🔄 **Automatische Updates** – Een achtergrondservice in een aparte container werkt de plugin-informatie elk uur bij.
- 👥 **Gebruikersbeheer** – Registratie, login en op rollen gebaseerde permissies (User, Co-Admin, Admin).
- 🎨 **Moderne UI** – Responsief ontwerp met een geavanceerd filtersysteem.
- 🛡️ **Adminpaneel** – Beheer gebruikers, plugins, categorieën en systeeminstellingen.

---

## 🛠️ Installatie & Gebruik

### Vereisten

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Stappen

**1. Kloon de Repository**

```bash
git clone https://github.com/VulcanoSoftware/VulcanoCraft-Plugin-Repository.git
cd VulcanoCraft-Plugin-Repository
```

**2. Configureer de Omgeving**

Maak een `.env`-bestand aan door het voorbeeld te kopiëren. Hier kun je de standaard MongoDB-instellingen aanpassen indien nodig.

```bash
cp .env.example .env
```

**3. Bouw en Start de Applicatie**

Gebruik Docker Compose om de images te bouwen en alle services te starten. De `-d` vlag zorgt ervoor dat de containers op de achtergrond draaien.

```bash
docker-compose build
docker-compose up -d
```

De applicatie is nu toegankelijk op `http://localhost:5000`.

**4. Maak een Admin-account aan**

Voer het volgende commando uit om een admin-account aan te maken. Je kunt de standaard `admin:admin123` gebruiken of je eigen credentials opgeven.

```bash
# Standaard admin-account aanmaken
docker-compose exec app python create_admin.py

# Een aangepast admin-account aanmaken
docker-compose exec app python create_admin.py <jouw-gebruikersnaam> <jouw-wachtwoord>
```

---

## 🐳 Docker Services Beheren

- **Applicatielogs bekijken:**
  ```bash
  docker-compose logs -f app
  ```

- **Cronjob-logs bekijken:**
  ```bash
  docker-compose logs -f cron
  ```

- **Alle services stoppen:**
  ```bash
  docker-compose down
  ```

- **Alle services stoppen en het databasevolume verwijderen (alle data gaat verloren!):**
  ```bash
  docker-compose down -v
  ```

---

## 🌐 Ondersteunde Platforms

- **SpigotMC** – `spigotmc.org/resources/*`
- **Modrinth** – `modrinth.com/plugin/*`
- **Hangar** – `hangar.papermc.io/*/*`
- **CurseForge** – `curseforge.com/minecraft/*`

---
<p align="right">made possible by <code>_.g.a.u.t.a.m._</code> on discord.</p>
<p align="right">made possible by <code>Swapnanilb</code> on https://github.com/Swapnanilb</p>
<p align="right">made possible by <code>luxetidal</code> on https://github.com/luxetidal</p>
<p align="right">made possible by <code>AlexTrinityBlock</code> on https://github.com/AlexTrinityBlock</p>
