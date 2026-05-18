# 🌱 Monitoreo Satelital

Sistema de monitoreo de cultivos de maní mediante imágenes satelitales Sentinel-2 y análisis geoespacial - Córdoba, Argentina.

## 📋 Descripción

Este proyecto permite:
- Procesar imágenes satelitales multitemporales
- Clasificar estados de cultivo (suelo, desarrollo, maduro, vegetación densa)
- Calcular áreas cultivadas
- Generar series temporales de índices de vegetación (NDVI, NDRE, NDWI, EVI)
- Visualizar resultados en una web interactiva

## 🗂️ Estructura

```
MANI_CORDOBA/
├── config_mani.py          # Configuración global del proyecto
├── utils_agro.py          # Utilidades comunes
├── requirements-web.txt   # Dependencias para la app web
├── datos/                 # Datos (satellite, clima, etc.)
│   ├── raw/              # Imágenes satelitales TIFF
│   ├── processed/       # DataCube NetCDF
│   └── externos/        # Datos externos (CSV)
├── scripts/              # Pipeline de procesamiento
│   ├── 1_cargar_datacube_optimizado.py
│   ├── 2_analisis_temporal_mejorado.py
│   ├── 3_clasificar_fecha_global.py
│   ├── 4_calcular_area_mejorado.py
│   ├── 5_timelapse.py
│   ├── 6_integracion_clima_agro.py
│   ├── 7_generar_informe_pdf_mejorado.py
│   └── 8_validacion_avanzada.py
├── web/                   # App web Streamlit
│   ├── app.py
│   └── pages/
│       ├── home.py
│       ├── upload.py
│       ├── results.py
│       ├── analytics.py
│       └── report.py
└── notebooks/             # Análisis exploratorio
    └── analisis_mani.ipynb
```

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/sdarionicolas-boop/MANI_CORDOBA.git
cd MANI_CORDOBA
```

### 2. Instalar dependencias
```bash
pip install -r requirements-web.txt
```

Dependencias principales:
- streamlit >= 1.28.0
- xarray, rioxarray, rasterio
- pandas, numpy, matplotlib
- geopandas, folium, plotly

## 💻 Uso

### Ejecutar la app web
```bash
streamlit run web/app.py
```
Luego acceder a: **http://localhost:8501**

### Ejecutar pipeline de procesamiento
```bash
cd MANI_CORDOBA
python scripts/1_cargar_datacube_optimizado.py
python scripts/2_analisis_temporal_mejorado.py
python scripts/3_clasificar_fecha_global.py
python scripts/4_calcular_area_mejorado.py
# ... continuar con los demás scripts
```

## 📊 Datos de Entrada

### Imágenes satelitales
- Formato: GeoTIFF (.tif)
- Bandas: B2, B3, B4, B5, B8 (Sentinel-2)
- Nombre: `MANI_YYYYMMDD.tif` (ej: MANI_20230708.tif)
- CRS: EPSG:32720 (UTM zona 20S)

### Datos tabulares
- CSV o Excel con datos de cultivos/clima

## 📈 Índices Calculados

| Índice | Fórmula | Aplicación |
|--------|---------|------------|
| NDVI | (NIR - Red) / (NIR + Red) | Vegetación |
| NDRE | (NIR - RedEdge) / (NIR + RedEdge) | Estrés vegetal |
| NDWI | (Green - NIR) / (Green + NIR) | Humedad |
| EVI | 2.5*(NIR-Red)/(NIR+6*Red-7.5*Blue+1) | Densidad vegetal |

## 🔧 Configuración

Editar `config_mani.py` para ajustar:
- Rutas de directorios
- Sistema de coordenadas (CRS)
- Bandas a utilizar
- Parámetros de clasificación (k-means)
- Umbrales de NDVI

## 📝 Changelog

### v1.0 (2025-05)
- App web Streamlit funcional
- Pipeline completo de 8 scripts
- Soporte para datos de Maní Córdoba

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor, abrí un issue o enviá un pull request.

## 📄 Licencia

Este proyecto está bajo la Licencia **GNU AGPL v3** - Mira el archivo [LICENSE](LICENSE) para más detalles. Esta licencia protege el software especialmente cuando se ofrece como servicio (SaaS/DaaS), obligando a compartir las mejoras realizadas.

## 👤 Autor

- **Dario Nicolas**
- GitHub: [@sdarionicolas-boop](https://github.com/sdarionicolas-boop)