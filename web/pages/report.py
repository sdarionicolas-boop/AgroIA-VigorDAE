
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
    """
    Calcula fenología enfocándose en la CAMPAÑA MÁS RECIENTE.
    Filtra los últimos 12 meses para evitar solapamiento entre años.
    """
    try:
        from scipy.ndimage import gaussian_filter1d
        from src.config.settings import FENO_PARAMS
        
        # Copia y filtro temporal
        df_f = df.copy()
        df_f["time"] = pd.to_datetime(df_f["time"])
        ultima_fecha = df_f["time"].max()
        # Tomamos solo el último ciclo anual
        df_f = df_f[df_f["time"] > (ultima_fecha - pd.Timedelta(days=365))]
        
        series = df_f["ndvi_auditado"].ffill().fillna(0).values
        dates = df_f["time"].values
        
        if len(series) < 5: return None

        smooth = gaussian_filter1d(series, sigma=FENO_PARAMS["sigma"])
        
        # Inicio: primer punto del ciclo actual sobre umbral
        start_mask = smooth > FENO_PARAMS["ndvi_start"]
        start_idx = int(np.argmax(start_mask)) if np.any(start_mask) else 0
        
        # Pico: máximo del ciclo actual
        peak_idx = int(np.nanargmax(smooth))
        
        # Fin: último punto o caída bajo umbral
        end_idx = len(smooth) - 1
        after_peak = smooth[peak_idx:]
        end_mask = after_peak < FENO_PARAMS["ndvi_end"]
        if np.any(end_mask):
            end_idx = peak_idx + int(np.argmax(end_mask))

        res = {
            "inicio": dates[start_idx], 
            "pico": dates[peak_idx], 
            "fin": dates[end_idx]
        }
        res["duracion_dias"] = (pd.Timestamp(res["fin"]) - pd.Timestamp(res["inicio"])).days
        
        # Validación agronómica básica
        if res["duracion_dias"] > 210: # Si dura más de 7 meses, algo está mal filtrado
             res["duracion_dias"] = "Ajuste requerido"
             
        return res
    except Exception as e:
        logger.warning(f"Error calculando feno: {e}")
        return None

def show(lote_id: str = "default"):
    st.title(f"Informe - {lote_id}")
    st.caption("Genera un reporte PDF con la auditoria completa del lote.")

    with st.form("informe_form"):
        # Sanitizado: No usar guiones largos en el valor por defecto
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
            feno = _calcular_fenologia(df)

            # Recargar el modulo para evitar caches de Streamlit
            import importlib
            import src.analysis.report_generator as rg
            importlib.reload(rg)
            
            pdf_bytes = rg.generate_report(lote_id, df, zonas or [], feno, mapa, titulo, region)

            st.success("Informe generado.")
            st.download_button(
                label="Descargar PDF",
                data=pdf_bytes,
                file_name=f"Informe_{lote_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
