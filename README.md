# 🌱 AgroIA - VigorDAE

**VigorDAE** es un sistema inteligente de monitoreo de cultivos (especializado en maní en Córdoba, Argentina) que garantiza la **integridad ecofisiológica** de los datos satelitales mediante el uso de Denoising Autoencoders (LSTM).

Este proyecto transforma series temporales ruidosas (Sentinel-2) en datos de vigor (NDVI, EVI) limpios y confiables, exponiéndolos a través de una arquitectura moderna lista para la nube (DaaS/SaaS).

## 🚀 Arquitectura del Sistema

El proyecto sigue una arquitectura modular de tres capas:

1. **Core Pipeline (`src/`):** Motor de ingesta, auditoría con IA (DAE) y zonificación (K-Means).
2. **DaaS API (`src/api/`):** Servicio FastAPI que expone los datos auditados por zona de manejo.
3. **SaaS Web App (`web/`):** Interfaz interactiva en Streamlit.

## 🗂️ Estructura de Directorios

```text
AgroIA-VigorDAE/
├── src/
│   ├── api/                # FastAPI Endpoints (DaaS)
│   ├── config/             # Configuración centralizada
│   ├── data/               # Ingestor de TIFF a DataCube NetCDF
│   ├── models/             # Agente Verificador DAE y Clustering
│   ├── analysis/           # Fenología y Tendencias
│   └── pipeline.py         # Orquestador del motor
├── web/                    # Aplicación Streamlit (SaaS)
├── datos/                  # [NO TRACKEADO] Datos raw (TIFF) y processed (NetCDF)
├── resultados/             # [NO TRACKEADO] Logs, reportes y gráficos
├── AGENT.md                # Cerebro del Proyecto (Lógica y Arquitectura)
├── Dockerfile              # Configuración de contenedor
└── requirements.txt        # Dependencias de Python
```

## ⚙️ Instalación y Uso Local

### 1. Preparar Entorno
```bash
git clone https://github.com/sdarionicolas-boop/AgroIA-VigorDAE.git
cd AgroIA-VigorDAE
pip install -r requirements.txt
cp .env.example .env
```
*(Asegúrate de colocar tus imágenes Sentinel-2 `MANI_YYYYMMDD.tif` en la carpeta `datos/raw/`)*

### 2. Ejecutar el Motor de Datos (Pipeline)
Este comando ingesta los TIFFs, entrena el Agente DAE, limpia anomalías y genera el DataCube auditado.
```bash
python -m src.pipeline
```

### 3. Levantar la API de Datos (DaaS)
```bash
uvicorn src.api.main:app --reload
```
*Documentación Swagger disponible en: `http://localhost:8000/docs`*

### 4. Levantar la Web App (SaaS)
```bash
streamlit run web/app.py
```
*Interfaz disponible en: `http://localhost:8501`*

## 🤖 El Agente Verificador (DAE)
El corazón de AgroIA-VigorDAE es un Autoencoder LSTM que:
1. Aprende la curva de crecimiento fenológico esperada.
2. Detecta anomalías (sombras, nubes no enmascaradas) evaluando el error de reconstrucción.
3. Reconstruye y corrige la serie temporal antes del análisis agronómico.

## 📄 Licencia

Este proyecto está bajo la Licencia **GNU AGPL v3** - Mira el archivo [LICENSE](LICENSE) para más detalles. Esta licencia protege el software especialmente cuando se ofrece como servicio (SaaS/DaaS), obligando a compartir las mejoras realizadas.

## 👤 Autor

- **AgroIA / Dario Nicolas**
- GitHub: [@sdarionicolas-boop](https://github.com/sdarionicolas-boop)