FROM python:3.10-slim

WORKDIR /app

# Instalar FFmpeg y otras dependencias necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libavcodec-extra \
    libmp3lame0 \
    libx264-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY microservices/conversion_service/requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del servicio
COPY microservices/conversion_service/ .

# Crear directorios para datos
RUN mkdir -p /data/temp /data/videos

# Set up alias
RUN echo 'alias py="python3"' >> /root/.bashrc

# Comando para iniciar el servicio
CMD ["python", "main.py"]