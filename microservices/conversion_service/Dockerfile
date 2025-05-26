FROM python:3.10-slim

WORKDIR /app

# Instalar FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY microservices/conversion_service/requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY microservices/conversion_service/ .

# Comando
CMD ["python", "main.py"]