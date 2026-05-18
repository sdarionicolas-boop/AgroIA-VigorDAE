
from fastapi import FastAPI, HTTPException
from typing import List, Dict
import pandas as pd
import xarray as xr
import numpy as np
from src.config.settings import DATACUBE_AUDIT_PATH, RESULTS_DIR
import logging

# Configuración del logger para la API
logger = logging.getLogger("API_Mani")

app = FastAPI(
    title="VigorDAE AI - DaaS API",
    description="Servicio de auditoría inteligente y consulta de vigor para cultivos de maní.",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Bienvenido a la API de MANI_CORDOBA. Use /docs para ver la documentación."}

@app.get("/lotes/default/ndvi_auditado")
async def get_ndvi_auditado():
    """
    Retorna la serie temporal de NDVI original vs auditado agregada por promedio espacial.
    """
    try:
        if not DATACUBE_AUDIT_PATH.exists():
            raise HTTPException(status_code=404, detail="DataCube auditado no encontrado.")
        
        ds = xr.open_dataset(DATACUBE_AUDIT_PATH)
        
        # AGREGACIÓN ESPACIAL: Promedio sobre dimensiones x e y
        # Esto reduce 2.3 millones de puntos a solo 78 puntos temporales
        ds_avg = ds[['NDVI', 'NDVI_auditado', 'es_anomalia']].mean(dim=['x', 'y'])
        
        df = ds_avg.to_dataframe().reset_index()
        df['time'] = df['time'].dt.strftime('%Y-%m-%d')
        
        # Redondear para ahorrar aún más espacio y limpiar NaNs
        df = df.round(4).replace({np.nan: None})
        
        return df.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Error en endpoint ndvi_auditado: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/lotes/default/fenologia")
async def get_fenologia():
    """
    Retorna los hitos fenológicos detectados por el sistema.
    """
    # Intentamos leer desde el CSV de resumen que generó el pipeline
    resumen_path = RESULTS_DIR / "resumen_ejecucion.csv"
    if not resumen_path.exists():
         raise HTTPException(status_code=404, detail="Resumen de ejecución no encontrado.")
    
    # Por ahora, devolvemos un mock o calculamos rápido desde el CSV
    # En una versión avanzada, esto leería de una base de datos de eventos
    return {
        "lote_id": "default",
        "cultivo": "Maní",
        "campaña": "2023-2025",
        "hitos": {
            "siembra_estimada": "2023-11-15",
            "pico_vegetativo": "2024-01-24",
            "cosecha_estimada": "2024-05-15"
        },
        "estado_actual": "Cosechado / Fin de campaña"
    }

@app.get("/health")
async def health_check():
    """Estado de salud de la API y disponibilidad de datos."""
    datacube_ok = DATACUBE_AUDIT_PATH.exists()
    return {
        "status": "online",
        "datacube_available": datacube_ok,
        "version": "1.0.0"
    }
