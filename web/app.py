import streamlit as st
import sys
import os

# Configuración de la página
st.set_page_config(
    page_title="AgroIA - VigorDAE | Monitor de Cultivos",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Añadir el directorio raíz al path para importaciones de src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web import pages

def main():
    st.sidebar.title("🌱 AgroIA - VigorDAE")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio(
        "Navegación",
        ["🏠 Inicio", "📈 Análisis", "📋 Informe"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption("v1.2.0 | Powered by DAE AI")

    if menu == "🏠 Inicio":
        st.header("Bienvenido a AgroIA - VigorDAE")
        st.markdown("""
        Esta plataforma utiliza **Inteligencia Artificial Avanzada** para auditar y analizar la salud de tus cultivos de maní.
        
        ### 🚀 Capacidades principales:
        *   **Auditoría DAE:** Limpieza automática de nubes y ruido satelital.
        *   **Zonificación de Precisión:** Identificación de zonas de manejo (Bajo/Medio/Alto vigor).
        *   **Análisis Temporal:** Evolución del vigor con integridad ecofisiológica garantizada.
        
        Vaya a la sección **📈 Análisis** en la barra lateral para comenzar.
        """)
        
    elif menu == "📈 Análisis":
        from web.pages import analytics
        analytics.show()
        
    elif menu == "📋 Informe":
        st.header("📋 Generación de Informes")
        st.info("Módulo de reportes PDF en desarrollo. Estará disponible en la próxima versión.")

if __name__ == "__main__":
    main()
