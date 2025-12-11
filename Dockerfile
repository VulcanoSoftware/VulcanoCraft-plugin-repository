# Gebruik een officiële Python runtime als basis-image
FROM python:3.11-slim

# Stel de werkdirectory in de container in
WORKDIR /app

# Installeer systeemafhankelijkheden die nodig zijn voor Playwright
RUN apt-get update && apt-get install -y \
    libgbm-dev \
    libasound2 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    lsb-release \
    xdg-utils \
    wget \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Kopieer de afhankelijkhedenbestanden
COPY requirements.txt .
COPY pyproject.toml .
COPY uv.lock .

# Installeer Python-afhankelijkheden met uv
# We gebruiken 'pip install uv' eerst om de package manager te installeren
RUN pip install uv
RUN uv pip install --no-cache-dir -r requirements.txt

# Installeer Playwright browsers
RUN playwright install

# Kopieer de rest van de applicatiecode naar de werkdirectory
COPY . .

# Maak de poort waarop de app draait beschikbaar
EXPOSE 5000

# Definieer de command om de applicatie te starten met Gunicorn
# Gunicorn is een productie-waardige WSGI-server
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "webserver:app"]
