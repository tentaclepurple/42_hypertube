FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema para libtorrent
RUN apt-get update && apt-get install -y \
    python3-libtorrent \
    python3-dev \
    build-essential \
    pkg-config \
    libssl-dev \
    libboost-python-dev \
    libboost-chrono-dev \
    libboost-random-dev \
    libboost-system-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY microservices/torrent_service/requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY microservices/torrent_service/ .

# Test que libtorrent funciona
RUN python3 -c "import libtorrent as lt; print(f'✅ Libtorrent {lt.version} importado correctamente')"

# Comando
CMD ["python", "main.py"]