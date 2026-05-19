
import io
import os
import logging
import requests
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime

logger = logging.getLogger(__name__)
_API_ROOT = os.getenv("API_URL", "http://localhost:8000")

def _fetch_resumen(lote_id: str):
    try:
        r = requests.get(f"{_API_ROOT}/lotes/{lote_id}/resumen", timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

def _fetch_zonas(lote_id: str):
    try:
        r = requests.get(f"{_API_ROOT}/lotes/{lote_id}/zonas", timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

def _fetch_mapa(lote_id: str):
    try:
        r = requests.get(f"{_API_ROOT}/lotes/{lote_id}/mapa/render", timeout=10)
        return r.content if r.status_code == 200 else None
    except: return None

def _calcular_fenologia(df: pd.DataFrame) -> dict | None:
    """
    Calcula fenologia enfocandose en la CAMPANA MAS RECIENTE.
    Garantiza el uso de pd.Timestamp para el calculo de duracion.
    """
    try:
        from scipy.ndimage import gaussian_filter1d
        from src.config.settings import FENO_PARAMS

        # Filtrar ultimos 12 meses para campana activa
        df = df.copy()
        df["time"] = pd.to_datetime(df["time"])
        cutoff = df["time"].max() - pd.DateOffset(months=12)
        df = df[df["time"] >= cutoff].reset_index(drop=True)

        if len(df) < 5:
            return None

        series = df["ndvi_auditado"].ffill().fillna(0).values
        dates  = df["time"].values

        smooth    = gaussian_filter1d(series, sigma=FENO_PARAMS["sigma"])
        start_mask = smooth > FENO_PARAMS["ndvi_start"]
        start_idx  = int(np.argmax(start_mask)) if np.any(start_mask) else 0
        peak_idx   = int(np.nanargmax(smooth))

        # Fin: buscar caida bajo umbral despues del pico
        end_idx = len(smooth) - 1
        after_peak = smooth[peak_idx:]
        end_mask = after_peak < FENO_PARAMS["ndvi_end"]
        if np.any(end_mask):
            end_idx = peak_idx + int(np.argmax(end_mask))

        inicio = pd.Timestamp(dates[start_idx])
        pico   = pd.Timestamp(dates[peak_idx])
        fin    = pd.Timestamp(dates[end_idx])

        result = {"inicio": inicio, "pico": pico, "fin": fin}

        # Duracion: resta entre pd.Timestamp garantiza .days
        result["duracion_dias"] = (fin - inicio).days

        return result
    except Exception as e:
        logger.warning(f"No se pudo calcular fenologia: {e}")
        return None

def show(lote_id: str = "default"):
    st.title(f"Informe - {lote_id}")
    st.caption("Genera un reporte PDF con la auditoria completa del lote.")

    with st.form("informe_form"):
        titulo = st.text_input("Titulo del Informe", value=f"Informe VigorDAE - {lote_id}")
        region = st.text_input("Region", value="Cordoba, Argentina")
        submit = st.form_submit_button("Generar Informe PDF", type="primary")

    if submit:
        with st.spinner("Preparando reporte..."):
            res = _fetch_resumen(lote_id)
            if not res:
                st.error("No se pudieron obtener datos para el informe.")
                return
            
            df = pd.DataFrame(res)
            zonas = _fetch_zonas(lote_id)
            mapa = _fetch_mapa(lote_id)
            
            # Llamada corregida al nombre de funcion actual
            feno = _calcular_fenologia(df)

            from src.analysis.report_generator import generate_report
            pdf_bytes = generate_report(lote_id, df, zonas or [], feno, mapa, titulo, region)

            st.success("Informe generado.")
            st.download_button(
                label="Descargar PDF",
                data=pdf_bytes,
                file_name=f"Informe_{lote_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
