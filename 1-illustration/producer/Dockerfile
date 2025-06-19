FROM python:3.12-slim

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libssl-dev && \
    rm -rf /var/lib/apt/lists/*

# Créer le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt .
COPY producer.py .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Lancer le producteur
CMD ["python", "producer.py"]
