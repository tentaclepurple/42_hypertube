FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY microservices/recommendation_service/requirements.txt .

# Instalar dependencias de Python (incluye bibliotecas para ML y vectores)
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del servicio
COPY microservices/recommendation_service/ .

# Set up alias
RUN echo 'alias py="python3"' >> /root/.bashrc

# Comando para iniciar el servicio
CMD ["python", "main.py"]