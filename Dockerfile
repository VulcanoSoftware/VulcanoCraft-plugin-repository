# Gebruik een officiële Python 3.11 slim-image als basis
FROM python:3.11-slim

# Stel de werkdirectory in de container in
WORKDIR /app

# Installeer uv om dependencies te beheren
RUN pip install uv

# Kopieer het requirements-bestand en installeer de Python-afhankelijkheden
COPY requirements.txt .
RUN uv pip install --no-cache-dir -r requirements.txt

# Installeer de benodigde Playwright-browsers
RUN playwright install

# Kopieer de volledige applicatiecode naar de werkdirectory
COPY . .

# Maak poort 5000 beschikbaar buiten de container
EXPOSE 5000

# Definieer het commando om de applicatie te starten met Gunicorn als productieserver
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "webserver:app"]
