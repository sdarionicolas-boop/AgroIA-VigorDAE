# 🧠 AGENT.MD: Cerebro del Proyecto VigorDAE AI

## 🚀 Misión del Proyecto
Transformar datos satelitales Sentinel-2 y climáticos en información accionable para el cultivo de maní en Córdoba, Argentina, garantizando la **integridad ecofisiológica** de los datos mediante Inteligencia Artificial (Agente DAE).

---

## ⚠️ Instrucción Clave para el Agente
**Para cualquier tarea de este proyecto, priorizá el contexto de este archivo sobre conocimiento general del modelo. Ante duda sobre arquitectura o flujo, consultá este AGENT.md antes de asumir.**

---

## 🏗️ Arquitectura del Sistema (Productiva)

El proyecto sigue una arquitectura desacoplada de tres capas:

1.  **Motor de Procesamiento (Core Pipeline):** Ubicado en `src/`. Transforma TIFFs raw en DataCubes NetCDF auditados.
2.  **DaaS (Data as a Service):** Capa de API construida con **FastAPI** (`src/api/`) que expone los datos auditados.
3.  **SaaS (Software as a Service):** Interfaz web interactiva en **Streamlit** (`web/`) que consume la API.

### Estructura de Carpetas
```text
VigorDAE AI/
├── src/
│   ├── api/                # FastAPI Endpoints (DaaS)
│   ├── config/             # Configuración centralizada (.env, settings.py, logging)
│   ├── data/               # Ingesta y manejo de DataCubes (xarray, NetCDF)
│   ├── models/             # IA: Agente Verificador DAE (LSTM) y Clusterting
│   ├── analysis/           # Lógica agronómica (Fenología, Estadísticas)
│   └── pipeline.py         # Orquestador principal del motor
├── web/                    # Interfaz Streamlit (SaaS)
├── datos/                  # Almacenamiento de archivos (Raw y Processed)
├── resultados/             # Salidas de análisis, logs y pruebas
└── Dockerfile              # Empaquetado profesional
```

---

## 🤖 El Agente Verificador (DAE)
Inspirado en el proyecto `agro-dae-auditor`. Es un **Denoising Autoencoder (LSTM)** encargado de:
*   **Aprender** el patrón de crecimiento real del maní.
*   **Detectar** "datos rotos" (nubes, sombras, fallos de sensor) que rompen la coherencia ecofisiológica.
*   **Reconstruir** los puntos anómalos para entregar una serie temporal limpia y confiable.

---

## 🔄 Flujo de Datos (Data Pipeline)
1.  **Ingesta:** `src/data/ingestor.py` lee `MANI_*.tif` -> Crea `datacube_s2_raw.nc`.
2.  **Auditoría:** `src/models/verifier.py` entrena/aplica el DAE al Raw -> Detecta anomalías.
3.  **Refinado:** El pipeline genera `datacube_s2_auditado.nc` con versiones limpias de NDVI.
4.  **Servicio:** La API (`src/api/main.py`) lee el Auditado y aplica agregación espacial (promedio) para optimizar la velocidad.
5.  **Visualización:** El SaaS (`web/pages/analytics.py`) muestra gráficos interactivos de Plotly consumiendo la API.

---

## 🛠️ Tecnologías Core
*   **Análisis Geoespacial:** xarray, rioxarray, rasterio, NetCDF4.
*   **Deep Learning:** PyTorch (LSTM Autoencoder).
*   **Backend:** FastAPI, Uvicorn.
*   **Frontend:** Streamlit, Plotly.
*   **Infraestructura:** Docker, Python-dotenv (env management).

---

## 📏 Estándares de Ingeniería
*   **No Hardcoding:** Todas las rutas deben derivar de `src/config/settings.py` y el archivo `.env`.
*   **Logging:** Usar siempre `logging` (configurado en `src/config/logging_config.py`), nunca `print`.
*   **Eficiencia API:** Realizar agregaciones (mean, resample) en el servidor (API) antes de enviar datos al cliente (SaaS).
*   **Validación:** Cada cambio en el pipeline debe ser verificado con un script de prueba o el pipeline principal.

---

## 📝 Próximos Pasos (Roadmap)
*   **Multitenancy:** Soporte para múltiples lotes/usuarios en la API y Base de Datos.
*   **Cloud Deployment:** Desplegar el Docker en AWS (ECS/Fargate) o GCP (Cloud Run).
*   **Alertas:** Sistema de notificaciones cuando el Agente DAE detecte anomalías en tiempo real.
