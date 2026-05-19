# Dockerfile para AgroIA - VigorDAE (Full Stack)
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

# Copiar el código fuente
COPY src/ ./src/
COPY web/ ./web/
COPY AGENT.md .
# Nota: datos/ y resultados/ se manejan mediante volúmenes en producción
RUN mkdir -p datos/raw datos/processed resultados/logs

# Exponer puertos: API (8000) y SaaS (8501)
EXPOSE 8000
EXPOSE 8501

# Script de arranque dual (API + Web)
RUN echo '#!/bin/bash \n\
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 & \n\
streamlit run web/app.py --server.port 8501 --server.address 0.0.0.0 \n\
' > start.sh && chmod +x start.sh

CMD ["./start.sh"]
