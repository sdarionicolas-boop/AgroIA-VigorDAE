import streamlit as st
import sys
import os
import requests

st.set_page_config(
    page_title="AgroIA - VigorDAE | Monitor de Cultivos",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Añadir el directorio raíz al path para importaciones de src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

API_BASE = os.getenv("API_URL", "http://localhost:8000")


@st.cache_data(ttl=60)
def fetch_lotes() -> list[str]:
    """Consulta /lotes y retorna la lista. Cachea 60 segundos."""
    try:
        r = requests.get(f"{API_BASE}/lotes", timeout=5)
        r.raise_for_status()
        return r.json().get("lotes", [])
    except requests.exceptions.ConnectionError:
        return []
    except Exception:
        return []


def main():
    st.sidebar.title("🌱 AgroIA - VigorDAE")
    st.sidebar.markdown("---")

    # ── Selector de lote ───────────────────────────────────────────────────────
    lotes = fetch_lotes()

    if not lotes:
        st.sidebar.warning("⚠️ Sin conexión con la API o sin lotes procesados.")
        st.sidebar.caption(f"API: `{API_BASE}`")
        lote_id = None
    else:
        lote_id = st.sidebar.selectbox(
            "Lote activo",
            options=lotes,
            index=0,
            help="Seleccioná el lote a analizar. Los lotes se generan ejecutando el pipeline.",
        )
        st.session_state["lote_id"] = lote_id

    st.sidebar.markdown("---")

    # ── Navegación ─────────────────────────────────────────────────────────────
    menu = st.sidebar.radio(
        "Navegación",
        ["🏠 Inicio", "📈 Análisis", "📋 Informe"],
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("v2.1.0 | Powered by DAE AI")

    # ── Páginas ────────────────────────────────────────────────────────────────
    if menu == "🏠 Inicio":
        st.header("Bienvenido a AgroIA - VigorDAE")
        st.markdown("""
        Esta plataforma utiliza **Inteligencia Artificial Avanzada** para auditar y analizar
        la salud de tus cultivos de maní.

        ### 🚀 Capacidades principales
        - **Auditoría DAE:** Limpieza automática de nubes y ruido satelital.
        - **Zonificación de Precisión:** Identificación de zonas de manejo (Bajo / Medio / Alto vigor).
        - **Análisis Temporal:** Evolución del vigor con integridad ecofisiológica garantizada.
        - **Multi-lote:** Monitoreo simultáneo de múltiples lotes desde un mismo panel.

        Seleccioná un lote en el selector de la barra lateral y navegá a **📈 Análisis**.
        """)

        if lotes:
            st.info(f"**{len(lotes)} lote(s) disponible(s):** {', '.join(lotes)}")
        else:
            st.warning(
                "No se detectaron lotes procesados. "
                "Ejecutá el pipeline con `python -m src.pipeline --lote <nombre>`."
            )

    elif menu == "📈 Análisis":
        if lote_id is None:
            st.warning("Conectá la API y procesá al menos un lote para ver el análisis.")
        else:
            from web.pages import analytics
            analytics.show(lote_id=lote_id)

    elif menu == "📋 Informe":
        st.header("📋 Generación de Informes")
        if lote_id:
            st.info(
                f"Lote seleccionado: **{lote_id}**. "
                "Módulo de reportes PDF en desarrollo — disponible en la próxima versión."
            )
        else:
            st.info("Módulo de reportes PDF en desarrollo.")


if __name__ == "__main__":
    main()
