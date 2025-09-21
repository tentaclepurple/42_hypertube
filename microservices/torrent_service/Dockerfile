# FROM python:3.11-slim
FROM mcr.microsoft.com/mirror/docker/library/python:3.11-slim

WORKDIR /app

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

COPY microservices/torrent_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY microservices/torrent_service/ .

RUN python3 -c "import libtorrent as lt; print(f'Libtorrent {lt.version}')"

CMD ["python", "main.py"]