FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dependencias de sistema — capa que cambia poco, va primero
RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# requirements primero — se cachea si no cambia el archivo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código fuente — capa que cambia más seguido, va al final
COPY src/ ./src/
COPY web/ ./web/
COPY AGENT.md .
COPY .env.example .env

# Carpetas para volúmenes montados
RUN mkdir -p datos/raw datos/processed resultados/logs

# Sin CMD — lo define docker-compose por servicio
