import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="SDF - Asistencia Rápida", layout="wide")

# --- ESTILO PARA CÍRCULOS VERDES ---
st.markdown("""
    <style>
    div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] > div:first-child {
        border-color: #28a745 !important;
        background-color: #28a745 !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] > div:first-child > div {
        background-color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# URLs estables (Mantenemos las que te funcionan)
URL_LISTADO = "https://docs.google.com/spreadsheets/d/1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI/export?format=csv&gid=320023"
URL_DOCENTES = "https://docs.google.com/spreadsheets/d/1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI/export?format=csv&gid=1283708974"

@st.cache_data(ttl=300)
def cargar_datos(url):
    df = pd.read_csv(f"{url}&timestamp={datetime.now().day}")
    df.columns = df.columns.str.strip()
    return df

# Conector solo para enviar
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df_maestro = cargar_datos(URL_LISTADO)
    df_docentes = cargar_datos(URL_DOCENTES)
    
    st.sidebar.header("Configuración")
    docente_sel = st.sidebar.selectbox("Docente", ["Selecciona..."] + df_docentes.iloc[:,0].dropna().unique().tolist())
    orquesta_sel = st.sidebar.selectbox("Orquesta", df_maestro["Orquesta"].unique())
    fecha_hoy = st.sidebar.date_input("Fecha de hoy", datetime.now())
    
    df_filtrado = df_maestro[
        (df_maestro["Orquesta"] == orquesta_sel) & 
        (df_maestro["Estado"].str.upper() == "ACTIVO")
    ].sort_values(by="NNA").copy()

    if docente_sel == "Selecciona...":
        st.info("👈 Selecciona docente")
    else:
        st.subheader(f"Lista {orquesta_sel}")
        
        asistencias = {}
        observaciones = {}

        for i, row in df_filtrado.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 3])
                with col1:
                    st.write(f"**{row['NNA']}**")
                    st.caption(row['Instrumento'])
                with col2:
                    asistencias[row['NNA']] = st.radio(
                        f"Asistencia_{row['NNA']}",
                        options=["P", "FX", "FNX"],
                        horizontal=True,
                        label_visibility="collapsed",
                        key=f"asist_{row['NNA']}"
                    )
                with col3:
                    observaciones[row['NNA']] = st.text_input(
                        "Obs", placeholder="Nota u obs...", 
                        label_visibility="collapsed", key=f"obs_{row['NNA']}"
                    )
                st.markdown("---")

        # --- PASO 1: GUARDAR Y REVISAR ---
        if st.button("🔍 1. GUARDAR Y REVISAR"):
            resumen = []
            for nombre in asistencias:
                # Buscamos el instrumento para que el historial sea completo
                inst = df_filtrado[df_filtrado["NNA"] == nombre]["Instrumento"].values[0]
                resumen.append({
                    "Fecha": fecha_hoy.strftime("%d/%m/%Y"),
                    "Orquesta": orquesta_sel,
                    "Docente": docente_sel,
                    "NNA": nombre,
                    "Instrumento": inst,
                    "V/F": asistencias[nombre],
                    "Observaciones": observaciones[nombre]
                })
            
            st.session_state.datos_revisados = pd.DataFrame(resumen)
            st.success("¡Listado procesado! Revísalo abajo antes de enviar.")
            st.table(st.session_state.datos_revisados)

        # --- PASO 2: ENVIAR DEFINITIVO ---
        if "datos_revisados" in st.session_state:
            st.warning("⚠️ ¿Todo correcto? Pulsa el botón de abajo para enviar a Google Sheets.")
            if st.button("🚀 2. CONFIRMAR Y ENVIAR A HISTORIAL"):
                try:
                    with st.spinner("Conectando con Google Sheets..."):
                        # Leemos historial
                        df_historial = conn.read(worksheet="HISTORIAL", ttl="0")
                        # Añadimos lo nuevo
                        df_final = pd.concat([df_historial, st.session_state.datos_revisados], ignore_index=True)
                        # Actualizamos
                        conn.update(worksheet="HISTORIAL", data=df_final)
                        
                        st.success("✅ ¡ENVIADO! Los datos ya están en la pestaña HISTORIAL.")
                        st.balloons()
                        # Limpiamos para evitar envíos duplicados
                        del st.session_state.datos_revisados
                except Exception as e_envio:
                    st.error(f"Error al enviar: {e_envio}")
                    st.info("Asegúrate de que la pestaña se llame HISTORIAL y que el Excel permita edición.")

except Exception as e:
    st.error(f"Error: {e}")
