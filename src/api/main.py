from fastapi import FastAPI, HTTPException, Response
from contextlib import asynccontextmanager
from typing import List, Dict, Optional
import pandas as pd
import xarray as xr
import numpy as np
from src.config.settings import DATACUBE_AUDIT_PATH
import logging
import io
from PIL import Image

logger = logging.getLogger("API_VigorDAE")

# Cache en memoria
_ds_cache: Optional[xr.Dataset] = None
_mapa_cache: Optional[np.ndarray] = None

# Paleta oficial VigorDAE (RGBA)
# -1: Gris (128,128,128), 0: Naranja (224,123,84), 1: Amarillo (242,201,76), 2: Verde (39,174,96)
PALETA_ZONAS = [
    128, 128, 128, 255,  # Index 0 (-1 -> shifted to 0)
    224, 123, 84, 255,   # Index 1 (0 -> shifted to 1)
    242, 201, 76, 255,   # Index 2 (1 -> shifted to 2)
    39, 174, 96, 255     # Index 3 (2 -> shifted to 3)
]

def _get_ds() -> xr.Dataset:
    if _ds_cache is None:
        raise HTTPException(status_code=503, detail="DataCube no cargado.")
    return _ds_cache

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ds_cache, _mapa_cache
    if DATACUBE_AUDIT_PATH.exists():
        logger.info("Cargando DataCube y Mapa en memoria...")
        _ds_cache = xr.open_dataset(DATACUBE_AUDIT_PATH)
        if 'zonas_manejo' in _ds_cache:
            _mapa_cache = _ds_cache.zonas_manejo.values
        logger.info("Carga completada.")
    yield
    if _ds_cache is not None:
        _ds_cache.close()

app = FastAPI(
    title="AgroIA - VigorDAE DaaS API",
    description="Servicio de auditoría inteligente y consulta de vigor por zonas de manejo.",
    version="1.3.0",
    lifespan=lifespan
)

@app.get("/lotes/default/mapa/meta")
async def get_mapa_meta():
    """Metadata técnica del mapa (CRS, BBox, Dimensiones)."""
    ds = _get_ds()
    if 'zonas_manejo' not in ds:
        raise HTTPException(status_code=404, detail="Zonificación no disponible.")
    
    crs_str = "EPSG:32720"
    bbox = None
    try:
        if ds.rio.crs is not None: crs_str = ds.rio.crs.to_string()
        bbox = list(ds.rio.bounds())
    except: pass

    return {
        "dimensions": {"y": int(ds.dims['y']), "x": int(ds.dims['x'])},
        "crs": crs_str,
        "bbox": bbox,
        "labels": {"0": "Bajo", "1": "Medio", "2": "Alto"}
    }

@app.get("/lotes/default/mapa/render")
async def get_mapa_render():
    """Retorna el mapa de zonificación como PNG binario con paleta indexada."""
    if _mapa_cache is None:
        raise HTTPException(status_code=404, detail="Matriz de mapa no disponible.")
    
    # Normalizar valores (-1, 0, 1, 2) a (0, 1, 2, 3) para índices de paleta
    idx_matrix = (_mapa_cache + 1).astype(np.uint8)
    
    img = Image.fromarray(idx_matrix, mode='P')
    # Aplicar la paleta (debe tener 768 valores para modo P, rellenamos el resto con 0)
    full_palette = PALETA_ZONAS + [0] * (768 - len(PALETA_ZONAS))
    img.putpalette(full_palette)
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    
    return Response(content=img_byte_arr.getvalue(), media_type="image/png")
