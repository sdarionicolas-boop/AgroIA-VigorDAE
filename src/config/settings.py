import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables desde .env (si existe)
load_dotenv()

# Rutas Base - Priorizar variables de entorno para Docker/Cloud
BASE_DIR = Path(os.getenv("BASE_DIR", os.getcwd())).resolve()

# Directorios de Datos
DATA_RAW_DIR = Path(os.getenv("DATA_RAW_DIR", BASE_DIR / "datos" / "raw"))
DATA_PROCESSED_DIR = Path(os.getenv("DATA_PROCESSED_DIR", BASE_DIR / "datos" / "processed"))
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", BASE_DIR / "resultados"))
LOG_DIR = Path(os.getenv("LOG_DIR", RESULTS_DIR / "logs"))

# Rutas de Archivos Específicos
DATACUBE_RAW_PATH = DATA_PROCESSED_DIR / "datacube_s2_raw.nc"
DATACUBE_AUDIT_PATH = DATA_PROCESSED_DIR / "datacube_s2_auditado.nc"

# Parámetros S2 / Geoespacial
CRS_EPSG = os.getenv("CRS_EPSG", "EPSG:32720")
BANDAS_S2 = ['B2', 'B3', 'B4', 'B5', 'B8', 'NDVI', 'NDRE', 'NDWI', 'EVI']

# Configuración del Agente DAE
DAE_PARAMS = {
    "seq_len": int(os.getenv("DAE_SEQ_LEN", 8)),
    "hidden_dim": int(os.getenv("DAE_HIDDEN_DIM", 32)),
    "epochs": int(os.getenv("DAE_EPOCHS", 100)),
    "lr": float(os.getenv("DAE_LR", 0.001))
}

# Parámetros de Fenología
FENO_PARAMS = {
    "ndvi_start": float(os.getenv("NDVI_START_THRESHOLD", 0.30)),
    "ndvi_end": float(os.getenv("NDVI_END_THRESHOLD", 0.40)),
    "sigma": 2
}

def ensure_dirs():
    """Crea la estructura de carpetas necesaria si no existe."""
    for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, RESULTS_DIR, LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)
