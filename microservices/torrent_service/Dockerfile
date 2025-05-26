FROM python:3.10-slim

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

# Crear symlink para que Python encuentre libtorrent
RUN ln -sf /usr/lib/python3/dist-packages/libtorrent.cpython-*.so /usr/local/lib/python3.10/site-packages/ || true

# Copiar requirements
COPY microservices/torrent_service/requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY microservices/torrent_service/ .

# Comando
CMD ["python", "main.py"]