
# Dockerfile para MANI_CORDOBA Pipeline
FROM python:3.11-slim

# Instalar dependencias de sistema (GDAL y otras necesarias para rasterio)
RUN apt-get update && apt-get install -y \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    && rm -rf /var/lib/apt/lists/*

# Configurar variables de entorno para GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /app

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY src/ ./src/
COPY data/ ./data/
# (Opcional) Copiar .env si se desea incluir valores por defecto
# COPY .env .

# Crear carpetas de salida
RUN mkdir -p datos/processed resultados/logs

# Comando por defecto para ejecutar el pipeline
CMD ["python", "-m", "src.pipeline"]
