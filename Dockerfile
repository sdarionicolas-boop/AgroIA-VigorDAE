# Dockerfile para AgroIA - VigorDAE (Microservices Base)
FROM python:3.11-slim

# Evitar prompts de debian
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias de sistema (GDAL y compilación)
RUN apt-get update && apt-get install -y \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Configurar variables de entorno para GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente y cerebro
COPY src/ ./src/
COPY web/ ./web/
COPY AGENT.md .
COPY .env.example .env

# Crear estructuras de carpetas para montajes
RUN mkdir -p datos/raw datos/processed resultados/logs

# La ejecución se define en docker-compose.yml
CMD ["python", "-m", "src.pipeline"]
