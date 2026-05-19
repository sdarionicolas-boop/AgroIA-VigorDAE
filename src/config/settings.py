import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Rutas base ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(os.getenv("BASE_DIR", os.getcwd())).resolve()

DATA_RAW_DIR      = Path(os.getenv("DATA_RAW_DIR",      BASE_DIR / "datos" / "raw"))
DATA_PROCESSED_DIR = Path(os.getenv("DATA_PROCESSED_DIR", BASE_DIR / "datos" / "processed"))
RESULTS_DIR       = Path(os.getenv("RESULTS_DIR",       BASE_DIR / "resultados"))
LOG_DIR           = Path(os.getenv("LOG_DIR",           RESULTS_DIR / "logs"))

# Rutas legacy (lote "default") — se mantienen para compatibilidad
DATACUBE_RAW_PATH  = DATA_PROCESSED_DIR / "datacube_s2_raw.nc"
DATACUBE_AUDIT_PATH = DATA_PROCESSED_DIR / "datacube_s2_auditado.nc"

# ── Rutas dinámicas por lote ───────────────────────────────────────────────────
def get_lote_paths(lote_id: str) -> dict:
    """
    Retorna las rutas de datos para un lote específico.

    Estructura en disco:
        datos/
          raw/{lote_id}/          ← TIFFs del lote
          processed/{lote_id}/    ← NetCDF raw y auditado
        resultados/{lote_id}/     ← CSVs y logs del lote
    """
    raw_dir       = DATA_RAW_DIR / lote_id
    processed_dir = DATA_PROCESSED_DIR / lote_id
    results_dir   = RESULTS_DIR / lote_id

    return {
        "raw_dir":       raw_dir,
        "processed_dir": processed_dir,
        "results_dir":   results_dir,
        "datacube_raw":  processed_dir / "datacube_s2_raw.nc",
        "datacube_audit": processed_dir / "datacube_s2_auditado.nc",
        "resumen_csv":   results_dir / "resumen_ejecucion.csv",
    }


def ensure_lote_dirs(lote_id: str) -> None:
    """Crea la estructura de carpetas para un lote si no existe."""
    paths = get_lote_paths(lote_id)
    for key in ("raw_dir", "processed_dir", "results_dir"):
        paths[key].mkdir(parents=True, exist_ok=True)


def ensure_dirs() -> None:
    """Crea la estructura base (sin lote específico)."""
    for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, RESULTS_DIR, LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def list_lotes() -> list[str]:
    """
    Retorna los lote_id disponibles: carpetas dentro de datos/processed/
    que contengan un datacube_s2_auditado.nc.
    """
    if not DATA_PROCESSED_DIR.exists():
        return []
    
    # Manejar caso de archivos en la raíz (legacy) y carpetas (nuevo)
    lotes = []
    if (DATA_PROCESSED_DIR / "datacube_s2_auditado.nc").exists():
        lotes.append("default")
        
    for d in sorted(DATA_PROCESSED_DIR.iterdir()):
        if d.is_dir() and (d / "datacube_s2_auditado.nc").exists():
            lotes.append(d.name)
            
    return sorted(list(set(lotes)))


# ── Parámetros geoespaciales ───────────────────────────────────────────────────
CRS_EPSG  = os.getenv("CRS_EPSG", "EPSG:32720")
BANDAS_S2 = ['B2', 'B3', 'B4', 'B5', 'B8', 'NDVI', 'NDRE', 'NDWI', 'EVI']

# ── Parámetros del Agente DAE ──────────────────────────────────────────────────
DAE_PARAMS = {
    "seq_len":    int(os.getenv("DAE_SEQ_LEN",    8)),
    "hidden_dim": int(os.getenv("DAE_HIDDEN_DIM", 32)),
    "epochs":     int(os.getenv("DAE_EPOCHS",     100)),
    "lr":         float(os.getenv("DAE_LR",       0.001)),
}

# ── Parámetros de fenología ────────────────────────────────────────────────────
FENO_PARAMS = {
    "ndvi_start": float(os.getenv("NDVI_START_THRESHOLD", 0.30)),
    "ndvi_end":   float(os.getenv("NDVI_END_THRESHOLD",   0.40)),
    "sigma": 2,
}
