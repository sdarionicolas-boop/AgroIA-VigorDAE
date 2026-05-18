
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

API_URL = "http://localhost:8000"

def show():
    st.title("📈 Análisis de Vigor (SaaS)")
    st.markdown("Visualización de datos auditados por el **Agente Verificador DAE**")
    
    # 1. Verificar conexión con la API
    try:
        health = requests.get(f"{API_URL}/health").json()
        if health["status"] != "online":
            st.error("⚠️ La API está fuera de línea.")
            return
    except:
        st.error("⚠️ No se pudo conectar con la API en http://localhost:8000. Asegúrese de que el servicio esté corriendo.")
        return

    st.success("✅ Conectado a la API de Datos (DaaS)")

    # 2. Consultar Datos Auditados
    with st.spinner("Obteniendo datos de la API..."):
        try:
            response = requests.get(f"{API_URL}/lotes/default/ndvi_auditado")
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                df['time'] = pd.to_datetime(df['time'])
                df = df.sort_values('time')
            else:
                st.error(f"Error al obtener datos: {response.text}")
                return
        except Exception as e:
            st.error(f"Fallo en la petición: {e}")
            return

    # 3. Sidebar con filtros y métricas rápidas
    st.sidebar.subheader("⚙️ Configuración de Vista")
    show_raw = st.sidebar.checkbox("Mostrar NDVI Satelital (Raw)", value=True)
    show_audit = st.sidebar.checkbox("Mostrar NDVI Auditado (DAE)", value=True)
    
    # Métricas
    total_points = len(df)
    anomalies = df[df['es_anomalia'] == True]
    pct_clean = (1 - len(anomalies)/total_points) * 100
    
    st.sidebar.metric("Salud del Dataset", f"{pct_clean:.1f}%")
    st.sidebar.metric("Anomalías Detectadas", len(anomalies))

    # 4. Gráfico Interactivo con Plotly
    st.subheader("📉 Evolución del Vigor (NDVI)")
    
    fig = go.Figure()

    if show_raw:
        fig.add_trace(go.Scatter(
            x=df['time'], y=df['NDVI'],
            mode='lines+markers',
            name='NDVI Satelital (Ruido)',
            line=dict(color='gray', dash='dash', width=1),
            marker=dict(size=4),
            opacity=0.5
        ))

    if show_audit:
        fig.add_trace(go.Scatter(
            x=df['time'], y=df['NDVI_auditado'],
            mode='lines',
            name='NDVI Auditado (Agente DAE)',
            line=dict(color='#2ecc71', width=3),
        ))

    # Resaltar anomalías
    if len(anomalies) > 0:
        fig.add_trace(go.Scatter(
            x=anomalies['time'], y=anomalies['NDVI'],
            mode='markers',
            name='Anomalía Detectada',
            marker=dict(color='#e74c3c', size=10, symbol='x-thin', line=dict(width=2))
        ))

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # 5. Información Fenológica (desde API)
    st.subheader("🌾 Fenología y Estado del Cultivo")
    try:
        pheno_data = requests.get(f"{API_URL}/lotes/default/fenologia").json()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"📅 **Siembra**\n\n{pheno_data['hitos']['siembra_estimada']}")
        with col2:
            st.success(f"🔝 **Pico Vigor**\n\n{pheno_data['hitos']['pico_vegetativo']}")
        with col3:
            st.warning(f"🚜 **Cosecha**\n\n{pheno_data['hitos']['cosecha_estimada']}")
    except:
        st.write("No se pudo obtener información fenológica.")

    # 6. Tabla de Auditoría
    with st.expander("🔍 Ver Tabla de Auditoría Detallada"):
        st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    show()
