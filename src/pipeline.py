
import logging
import pandas as pd
import numpy as np
import xarray as xr
from src.config.logging_config import setup_logging
from src.config.settings import (
    ensure_dirs, DAE_PARAMS, DATACUBE_AUDIT_PATH, 
    RESULTS_DIR, FENO_PARAMS
)
from src.data.ingestor import DataIngestor
from src.models.verifier import DAEVerifier
from src.analysis.phenology import PhenologyAnalyzer
from src.analysis.stats import StatsAnalyzer

def run_pipeline():
    # 1. Preparación
    setup_logging()
    ensure_dirs()
    logger = logging.getLogger("PipelinePrincipal")
    logger.info("Iniciando Pipeline Productivo MANI_CORDOBA")

    # 2. Ingesta (Raw DataCube)
    ingestor = DataIngestor()
    ds_raw = ingestor.process_to_datacube()
    
    if ds_raw is None:
        logger.error("Fallo en la ingesta. Abortando.")
        return

    # 3. Auditoría con Agente DAE
    logger.info("Iniciando fase de Auditoría (Agente Verificador)...")
    ndvi_avg = ds_raw['NDVI'].mean(dim=['x', 'y']).values
    valid_mask = ~np.isnan(ndvi_avg)
    
    verifier = DAEVerifier(
        input_dim=1, 
        hidden_dim=DAE_PARAMS["hidden_dim"], 
        seq_len=DAE_PARAMS["seq_len"]
    )
    
    verifier.train(ndvi_avg[valid_mask], epochs=DAE_PARAMS["epochs"])
    cleaned_ndvi, anomaly_mask = verifier.audit(ndvi_avg)
    
    # 4. Análisis (Usando datos auditados)
    logger.info("Iniciando fase de Análisis Agronómico...")
    dates = pd.to_datetime(ds_raw.time.values)
    
    # Fenología
    pheno = PhenologyAnalyzer(FENO_PARAMS)
    season_results = pheno.analyze_season(cleaned_ndvi, dates)
    if season_results:
        logger.info(f"Fenología detectada: Inicio={season_results['inicio']}, Pico={season_results['pico']}")

    # Estadísticas y Tendencias
    stats_eng = StatsAnalyzer()
    trend = stats_eng.calculate_trend(cleaned_ndvi)
    if trend:
        logger.info(f"Tendencia NDVI: {'Creciente' if trend['slope'] > 0 else 'Decreciente'} (R2={trend['r_squared']:.2f})")

    # 5. Guardar Resultados Finales
    logger.info("Generando DataCube Auditado y Reportes...")
    ds_audit = ds_raw.copy()
    ds_audit['NDVI_auditado'] = (('time'), cleaned_ndvi)
    ds_audit['es_anomalia'] = (('time'), anomaly_mask)
    
    ds_audit.to_netcdf(DATACUBE_AUDIT_PATH)
    
    # Exportar resumen a CSV
    summary_df = pd.DataFrame({
        'fecha': dates,
        'ndvi_raw': ndvi_avg,
        'ndvi_clean': cleaned_ndvi,
        'anomaly': anomaly_mask
    })
    summary_df.to_csv(RESULTS_DIR / "resumen_ejecucion.csv", index=False)
    
    logger.info(f"Pipeline finalizado satisfactoriamente.")
    logger.info(f"Resultados en: {DATACUBE_AUDIT_PATH}")

if __name__ == "__main__":
    run_pipeline()
