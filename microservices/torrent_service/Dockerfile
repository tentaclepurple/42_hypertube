FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema para libtorrent
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libboost-all-dev \
    libssl-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY microservices/torrent_service/requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del servicio
COPY microservices/torrent_service/ .

# Crear directorio para datos temporales
RUN mkdir -p /data/temp

# Set up alias
RUN echo 'alias py="python3"' >> /root/.bashrc

# Comando para iniciar el servicio
CMD ["python", "main.py"]