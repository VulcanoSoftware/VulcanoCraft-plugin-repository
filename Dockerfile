FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt && python -m playwright install --with-deps chromium

COPY . .

ENV FLASK_ENV=production
ENV MONGO_URI=mongodb://mongo:27017
ENV MONGO_DB_NAME=vulcanocraft

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "webserver:app"]

