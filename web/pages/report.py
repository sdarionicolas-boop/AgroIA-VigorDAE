
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

def _calcular_feno(df: pd.DataFrame):
    try:
        from scipy.ndimage import gaussian_filter1d
        from src.config.settings import FENO_PARAMS
        series = df["ndvi_auditado"].ffill().fillna(0).values
        dates = pd.to_datetime(df["time"]).values
        smooth = gaussian_filter1d(series, sigma=FENO_PARAMS["sigma"])
        start_idx = int(np.argmax(smooth > FENO_PARAMS["ndvi_start"]))
        peak_idx = int(np.nanargmax(smooth))
        res = {"inicio": dates[start_idx], "pico": dates[peak_idx], "fin": dates[-1]}
        res["duracion_dias"] = (pd.to_datetime(res["fin"]) - pd.to_datetime(res["inicio"])).days
        return res
    except: return None

def show(lote_id: str = "default"):
    st.title(f"📋 Informe · {lote_id}")
    st.caption("Generá un reporte PDF con la auditoría completa del lote.")

    with st.form("informe_form"):
        titulo = st.text_input("Título del Informe", value=f"Informe VigorDAE — {lote_id}")
        region = st.text_input("Región", value="Córdoba, Argentina")
        submit = st.form_submit_button("📊 Generar Informe PDF", type="primary")

    if submit:
        with st.spinner("Preparando reporte..."):
            res = _fetch_resumen(lote_id)
            if not res:
                st.error("No se pudieron obtener datos para el informe.")
                return
            
            df = pd.DataFrame(res)
            zonas = _fetch_zonas(lote_id)
            mapa = _fetch_mapa(lote_id)
            feno = _calcular_feno(df)

            from src.analysis.report_generator import generate_report
            pdf_bytes = generate_report(lote_id, df, zonas or [], feno, mapa, titulo, region)

            st.success("✅ Informe generado.")
            st.download_button(
                label="⬇️ Descargar PDF",
                data=pdf_bytes,
                file_name=f"Informe_{lote_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
