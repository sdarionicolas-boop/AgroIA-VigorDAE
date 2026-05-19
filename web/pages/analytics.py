import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# ── Configuración ──────────────────────────────────────────────────────────────
_API_ROOT = os.getenv("API_URL", "http://localhost:8000")
ZONA_COLORES = {"Bajo": "#E07B54", "Medio": "#F2C94C", "Alto": "#27AE60"}
ZONA_COLORES_MAPA = {-1: [200, 200, 200], 0: [224, 123, 84], 1: [242, 201, 76], 2: [39, 174, 96]}


# ── Helpers ────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch(endpoint: str, lote_id: str):
    """Llama a /lotes/{lote_id}/{endpoint} y retorna el JSON. Cachea 5 minutos."""
    url = f"{_API_ROOT}/lotes/{lote_id}/{endpoint}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("No se puede conectar con la API. ¿Está corriendo uvicorn?")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"Error de API ({e.response.status_code}): {e.response.text}")
        return None


def anomaly_shapes(df: pd.DataFrame) -> list:
    """Genera rectángulos de fondo para marcar timesteps con anomalía."""
    shapes = []
    for _, row in df[df["anomalia"] == True].iterrows():
        shapes.append(dict(
            type="rect", xref="x", yref="paper",
            x0=row["time"], x1=row["time"],
            y0=0, y1=1,
            line=dict(color="rgba(255,80,80,0.4)", width=1, dash="dot"),
        ))
    return shapes


def show(lote_id: str = "default") -> None:
    """Punto de entrada llamado desde app.py con el lote seleccionado."""

    st.title(f"🌱 VigorDAE · {lote_id}")
    st.caption("Monitoreo satelital auditado por IA · Sentinel-2 · Córdoba, Argentina")

    tab_resumen, tab_zonas, tab_mapa = st.tabs(["📊 Resumen Global", "🗺️ Zonas de Manejo", "🔲 Mapa de Zonificación"])


    # ══════════════════════════════════════════════════════════════════════════════
    # TAB 1 — RESUMEN GLOBAL
    # ══════════════════════════════════════════════════════════════════════════════
    with tab_resumen:
        data_resumen = fetch("resumen", lote_id)

        if not data_resumen:
            st.warning("Sin datos de resumen disponibles.")
        else:
            df_res = pd.DataFrame(data_resumen)
            df_res["time"] = pd.to_datetime(df_res["time"])

            # KPIs
            ndvi_max = df_res["ndvi_auditado"].max()
            ndvi_prom = df_res["ndvi_auditado"].mean()
            n_anomalias = int(df_res["es_anomalia"].sum())
            pct_anomalias = round(n_anomalias / len(df_res) * 100, 1)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("NDVI Máximo", f"{ndvi_max:.3f}")
            col2.metric("NDVI Promedio", f"{ndvi_prom:.3f}")
            col3.metric("Anomalías Detectadas", n_anomalias)
            col4.metric("% Serie Auditada", f"{100-pct_anomalias}%")

            st.divider()

            # Gráfico: NDVI crudo vs auditado
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_res["time"], y=df_res["ndvi_raw"],
                name="NDVI Crudo", mode="lines+markers",
                line=dict(color="#AAAAAA", width=1, dash="dot"),
                marker=dict(size=4),
            ))
            fig.add_trace(go.Scatter(
                x=df_res["time"], y=df_res["ndvi_auditado"],
                name="NDVI Auditado (DAE)", mode="lines+markers",
                line=dict(color="#2980B9", width=2.5),
                marker=dict(size=5),
            ))

            # Marcar anomalías
            anomalias = df_res[df_res["es_anomalia"] == True]
            if not anomalias.empty:
                fig.add_trace(go.Scatter(
                    x=anomalias["time"], y=anomalias["ndvi_raw"],
                    name="Anomalía Corregida", mode="markers",
                    marker=dict(color="#E74C3C", size=9, symbol="x"),
                ))

            fig.update_layout(
                title="Serie temporal NDVI global — Crudo vs Auditado por DAE",
                xaxis_title="Fecha", yaxis_title="NDVI",
                yaxis=dict(range=[-0.1, 1.0]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=420, margin=dict(l=40, r=20, t=60, b=40),
                shapes=anomaly_shapes(df_res.rename(columns={"es_anomalia": "anomalia"})),
            )
            st.plotly_chart(fig, use_container_width=True)


    # ══════════════════════════════════════════════════════════════════════════════
    # TAB 2 — ZONAS DE MANEJO
    # ══════════════════════════════════════════════════════════════════════════════
    with tab_zonas:
        data_zonas = fetch("zonas", lote_id)

        if not data_zonas:
            st.warning("Sin datos de zonas disponibles.")
        else:
            cols = st.columns(len(data_zonas))
            for i, zona in enumerate(data_zonas):
                cols[i].metric(f"Zona {zona['nombre']}", f"{zona['pct_pixeles']}% del lote")

            st.divider()

            fig = go.Figure()
            for zona in data_zonas:
                df_z = pd.DataFrame(zona["data"])
                df_z["time"] = pd.to_datetime(df_z["time"])
                color = ZONA_COLORES.get(zona["nombre"], "#888888")
                fig.add_trace(go.Scatter(
                    x=df_z["time"], y=df_z["ndvi"],
                    name=f"Zona {zona['nombre']}",
                    mode="lines+markers",
                    line=dict(color=color, width=2.5),
                    marker=dict(size=5),
                ))

            fig.update_layout(
                title="Curvas de vigor NDVI auditado por zona de manejo",
                xaxis_title="Fecha", yaxis_title="NDVI",
                yaxis=dict(range=[-0.1, 1.0]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=440, margin=dict(l=40, r=20, t=60, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)


    # ══════════════════════════════════════════════════════════════════════════════
    # TAB 3 — MAPA DE ZONIFICACIÓN
    # ══════════════════════════════════════════════════════════════════════════════
    with tab_mapa:
        with st.spinner("Cargando render de mapa..."):
            meta = fetch("mapa/meta", lote_id)
            mapa_url = f"{_API_ROOT}/lotes/{lote_id}/mapa/render"

        if not meta:
            st.warning("Información de mapa no disponible.")
        else:
            dims = meta["dimensions"]
            col_info, col_mapa = st.columns([1, 3])

            with col_info:
                st.subheader("Información del Lote")
                st.write(f"**Sistema:** `{meta['crs']}`")
                st.write(f"**Resolución:** {dims['y']} × {dims['x']} píxeles")
                st.divider()
                st.markdown("**Leyenda Operativa**")
                st.write("🟢 **Zona Alto Vigor**")
                st.write("🟡 **Zona Vigor Medio**")
                st.write("🟠 **Zona Bajo Vigor**")
                st.write("⬜ **Fuera de Lote / Ruido**")

            with col_mapa:
                st.image(mapa_url, caption="Mapa de Zonificación de Precisión (PNG Optimizado)", use_container_width=True)
                st.caption("Renderizado en servidor con paleta indexada de AgroIA.")
