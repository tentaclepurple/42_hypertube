FROM python:3.10-slim

WORKDIR /app

# Instalar libtorrent desde repositorios del sistema
RUN apt-get update && apt-get install -y \
    python3-libtorrent \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements SIN python-libtorrent
COPY microservices/torrent_service/requirements.txt .

# Instalar el resto de dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY microservices/torrent_service/ .

# Comando
CMD ["python", "main.py"]