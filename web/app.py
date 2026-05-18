import streamlit as st
import sys
import os

st.set_page_config(
    page_title="VigorDAE AI - Monitor de Cultivos",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from web import pages

def main():
    st.sidebar.title("🌱 VigorDAE AI")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio(
        "Navegación",
        ["🏠 Inicio", "📤 Subir Datos", "📊 Resultados", "📈 Análisis", "📋 Informe"]
    )
    
    if menu == "🏠 Inicio":
        pages.home.show()
    elif menu == "📤 Subir Datos":
        pages.upload.show()
    elif menu == "📊 Resultados":
        pages.results.show()
    elif menu == "📈 Análisis":
        pages.analytics.show()
    elif menu == "📋 Informe":
        pages.report.show()

if __name__ == "__main__":
    main()