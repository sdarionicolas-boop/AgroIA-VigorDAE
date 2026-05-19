from fastapi import FastAPI, HTTPException, Response
from contextlib import asynccontextmanager
from typing import Optional
import pandas as pd
import xarray as xr
import numpy as np
import logging
import io
from PIL import Image

from src.config.settings import list_lotes, get_lote_paths

logger = logging.getLogger("API_VigorDAE")

# ── Cache por lote ─────────────────────────────────────────────────────────────
# { lote_id: { "ds": xr.Dataset, "mapa": np.ndarray | None } }
_lote_cache: dict[str, dict] = {}

_PALETA = [
    128, 128, 128, 255,
    224, 123,  84, 255,
    242, 201,  76, 255,
     39, 174,  96, 255,
]
_FULL_PALETTE = _PALETA + [0] * (768 - len(_PALETA))


def _load_lote(lote_id: str) -> None:
    """Carga el DataCube de un lote en cache. No-op si ya está cargado."""
    if lote_id in _lote_cache:
        return
    paths = get_lote_paths(lote_id)
    # Compatibilidad con legacy: si default no está en carpeta, usar ruta raíz
    audit_path = paths["datacube_audit"]
    if lote_id == "default" and not audit_path.exists():
        from src.config.settings import DATACUBE_AUDIT_PATH
        audit_path = DATACUBE_AUDIT_PATH
        
    if not audit_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"DataCube del lote '{lote_id}' no encontrado. "
                   f"Ejecutá: python -m src.pipeline --lote {lote_id}",
        )
    logger.info(f"Cargando lote '{lote_id}' en cache...")
    ds = xr.open_dataset(audit_path)
    mapa = ds.zonas_manejo.values if "zonas_manejo" in ds else None
    _lote_cache[lote_id] = {"ds": ds, "mapa": mapa}
    logger.info(f"Lote '{lote_id}' cargado.")


def _get_lote(lote_id: str) -> dict:
    _load_lote(lote_id)
    return _lote_cache[lote_id]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-carga todos los lotes disponibles al arrancar la API."""
    lotes = list_lotes()
    if lotes:
        logger.info(f"Pre-cargando lotes: {lotes}")
        for lote_id in lotes:
            try:
                _load_lote(lote_id)
            except Exception as e:
                logger.warning(f"No se pudo pre-cargar lote '{lote_id}': {e}")
    else:
        logger.warning("No se encontraron lotes procesados. Ejecutá el pipeline primero.")
    yield
    for entry in _lote_cache.values():
        entry["ds"].close()
    logger.info("Todos los datasets cerrados.")


app = FastAPI(
    title="AgroIA - VigorDAE DaaS API",
    description="Auditoría inteligente de vigor satelital por zonas de manejo.",
    version="2.0.0",
    lifespan=lifespan,
)


# ── Sistema ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "AgroIA - VigorDAE API operativa.", "version": "2.0.0"}


@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "lotes_cargados": list(_lote_cache.keys()),
        "lotes_disponibles": list_lotes(),
    }


@app.get("/lotes")
async def get_lotes():
    """Lista todos los lotes con DataCube auditado disponible."""
    return {"lotes": list_lotes()}


# ── Por lote ───────────────────────────────────────────────────────────────────

@app.get("/lotes/{lote_id}/resumen")
async def get_resumen(lote_id: str):
    """Serie temporal NDVI auditado global del lote."""
    ds = _get_lote(lote_id)["ds"]

    df = pd.DataFrame({
        "time":          ds.time.dt.strftime("%Y-%m-%d").values,
        "ndvi_raw":      ds.NDVI.mean(dim=["x", "y"]).values.round(4),
        "ndvi_auditado": ds.NDVI_auditado_global.values.round(4),
        "es_anomalia":   ds.es_anomalia_global.values.astype(bool),
    }).replace({np.nan: None})

    return df.to_dict(orient="records")


@app.get("/lotes/{lote_id}/zonas")
async def get_zonas(lote_id: str):
    """Series temporales auditadas por zona de manejo."""
    entry = _get_lote(lote_id)
    ds, mapa = entry["ds"], entry["mapa"]
    time_str = ds.time.dt.strftime("%Y-%m-%d").values
    total_validos = int((mapa >= 0).sum()) if mapa is not None else 0
    nombres = ["Bajo", "Medio", "Alto"]
    resultado = []

    for z in range(3):
        var_ndvi     = f"NDVI_auditado_z{z}"
        var_anomalia = f"es_anomalia_z{z}"
        if var_ndvi not in ds:
            continue
        pct = round(float((mapa == z).sum() / total_validos * 100), 1) if total_validos > 0 else None
        resultado.append({
            "zona":        z,
            "nombre":      nombres[z],
            "pct_pixeles": pct,
            "data": pd.DataFrame({
                "time":     time_str,
                "ndvi":     ds[var_ndvi].values.round(4),
                "anomalia": ds[var_anomalia].values.astype(bool),
            }).replace({np.nan: None}).to_dict(orient="records"),
        })

    return resultado


@app.get("/lotes/{lote_id}/mapa/meta")
async def get_mapa_meta(lote_id: str):
    """Metadata técnica del mapa (CRS, BBox, dimensiones)."""
    ds = _get_lote(lote_id)["ds"]
    if "zonas_manejo" not in ds:
        raise HTTPException(status_code=404, detail="Zonificación no disponible.")

    crs_str, bbox = "EPSG:32720", None
    try:
        if ds.rio.crs is not None:
            crs_str = ds.rio.crs.to_string()
        bbox = list(ds.rio.bounds())
    except Exception:
        pass

    return {
        "lote_id":    lote_id,
        "dimensions": {"y": int(ds.dims["y"]), "x": int(ds.dims["x"])},
        "crs":        crs_str,
        "bbox":       bbox,
        "labels":     {"-1": "Sin dato", "0": "Bajo", "1": "Medio", "2": "Alto"},
    }


@app.get("/lotes/{lote_id}/mapa/render")
async def get_mapa_render(lote_id: str):
    """PNG con paleta indexada del mapa de zonificación."""
    mapa = _get_lote(lote_id)["mapa"]
    if mapa is None:
        raise HTTPException(status_code=404, detail="Mapa de zonas no disponible.")

    img = Image.fromarray((mapa + 1).astype(np.uint8), mode="P")
    img.putpalette(_FULL_PALETTE)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
