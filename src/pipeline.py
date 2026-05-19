import logging
import pandas as pd
import numpy as np
import xarray as xr
from src.config.logging_config import setup_logging
from src.config.settings import (
    ensure_dirs, ensure_lote_dirs, get_lote_paths,
    DAE_PARAMS, FENO_PARAMS
)
from src.data.ingestor import DataIngestor
from src.models.verifier import DAEVerifier
from src.models.zonification import AgroZonificator
from src.analysis.phenology import PhenologyAnalyzer
from src.analysis.stats import StatsAnalyzer


def run_pipeline(lote_id: str = "default") -> None:
    """
    Ejecuta el pipeline completo para un lote específico.

    Args:
        lote_id: Identificador del lote. Determina las rutas de entrada
                 (datos/raw/{lote_id}/) y salida (datos/processed/{lote_id}/).
    """
    setup_logging()
    ensure_dirs()
    ensure_lote_dirs(lote_id)

    logger = logging.getLogger(f"Pipeline.{lote_id}")
    logger.info(f"Iniciando Pipeline VigorDAE · lote='{lote_id}'")

    paths = get_lote_paths(lote_id)

    # ── 1. Ingesta ─────────────────────────────────────────────────────────────
    # Si el lote es default, buscamos en la raíz de raw por compatibilidad
    raw_path = paths["raw_dir"] if lote_id != "default" else DATA_RAW_DIR
    
    ingestor = DataIngestor(
        raw_dir=raw_path,
        output_path=paths["datacube_raw"],
    )
    ds_raw = ingestor.process_to_datacube()

    if ds_raw is None:
        logger.error(f"Fallo en la ingesta para lote {lote_id}. Abortando.")
        return

    # ── 2. Zonificación espacial (K-Means sobre NDVI crudo) ───────────────────
    logger.info("Iniciando zonificación espacial...")
    zonificator = AgroZonificator(n_clusters=3)
    zone_map = zonificator.generate_zones(ds_raw, variable='NDVI')

    # ── 3. Auditoría DAE (global + por zona) ──────────────────────────────────
    logger.info("Iniciando auditoría multi-zona con Agente DAE...")
    verifier = DAEVerifier(
        input_dim=1,
        hidden_dim=DAE_PARAMS["hidden_dim"],
        seq_len=DAE_PARAMS["seq_len"],
    )

    ds_audit = ds_raw.copy()
    if zone_map is not None:
        ds_audit['zonas_manejo'] = (('y', 'x'), zone_map)

    # Serie global
    ndvi_global = ds_raw['NDVI'].mean(dim=['x', 'y']).values
    valid_mask_g = ~np.isnan(ndvi_global)
    verifier.train(ndvi_global[valid_mask_g], epochs=DAE_PARAMS["epochs"])
    cleaned_g, mask_g = verifier.audit(ndvi_global)
    ds_audit['NDVI_auditado_global'] = (('time',), cleaned_g)
    ds_audit['es_anomalia_global']   = (('time',), mask_g)

    # Series por zona
    for z in range(3):
        logger.info(f"Auditando zona {z}...")
        mask_zona = (zone_map == z)
        ndvi_zona = ds_raw['NDVI'].where(mask_zona).mean(dim=['x', 'y']).values
        if (~np.isnan(ndvi_zona)).any():
            cleaned_z, mask_z = verifier.audit(ndvi_zona)
            ds_audit[f'NDVI_auditado_z{z}'] = (('time',), cleaned_z)
            ds_audit[f'es_anomalia_z{z}']   = (('time',), mask_z)

    # ── 4. Análisis agronómico ─────────────────────────────────────────────────
    logger.info("Iniciando análisis agronómico...")
    dates = pd.to_datetime(ds_raw.time.values)
    pheno = PhenologyAnalyzer(FENO_PARAMS)
    season_results = pheno.analyze_season(cleaned_g, dates)
    if season_results:
        logger.info(
            f"Fenología · inicio={season_results['inicio']} "
            f"pico={season_results['pico']}"
        )

    # ── 5. Guardar resultados ──────────────────────────────────────────────────
    logger.info(f"Guardando DataCube auditado en {paths['datacube_audit']}...")
    ds_audit.to_netcdf(paths["datacube_audit"])

    summary_df = pd.DataFrame({
        'fecha':      dates,
        'ndvi_raw':   ndvi_global,
        'ndvi_clean': cleaned_g,
        'anomaly':    mask_g,
    })
    for z in range(3):
        key = f'NDVI_auditado_z{z}'
        if key in ds_audit:
            summary_df[f'ndvi_z{z}'] = ds_audit[key].values

    summary_df.to_csv(paths["resumen_csv"], index=False)

    logger.info(f"Pipeline '{lote_id}' finalizado. Resultados en {paths['datacube_audit']}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline VigorDAE")
    parser.add_argument(
        "--lote", type=str, default="default",
        help="ID del lote a procesar (default: 'default')"
    )
    args = parser.parse_args()
    run_pipeline(lote_id=args.lote)
