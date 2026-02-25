import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="SDF - Control de Asistencia", layout="wide")

# --- CSS DEFINITIVO PARA EL COLOR VERDE ---
# Esto fuerza a que el color primario de los controles sea Verde SDF
st.markdown("""
    <style>
    :root {
        --primary-color: #28a745;
    }
    .st-emotion-cache-6q9sum.edgvbvh3 { background-color: #28a745 !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] > div:first-child {
        border-color: #28a745 !important;
        background-color: #28a745 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# URLs de lectura (las que te funcionan)
URL_LISTADO = "https://docs.google.com/spreadsheets/d/1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI/export?format=csv&gid=320023"
URL_DOCENTES = "https://docs.google.com/spreadsheets/d/1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI/export?format=csv&gid=1283708974"

@st.cache_data(ttl=300)
def cargar_datos(url):
    df = pd.read_csv(f"{url}&timestamp={datetime.now().day}")
    df.columns = df.columns.str.strip()
    return df

# Conexión para el envío
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df_maestro = cargar_datos(URL_LISTADO)
    df_docentes = cargar_datos(URL_DOCENTES)
    
    st.sidebar.header("Configuración")
    docente_sel = st.sidebar.selectbox("Docente", ["Selecciona..."] + df_docentes.iloc[:,0].dropna().unique().tolist())
    orquesta_sel = st.sidebar.selectbox("Orquesta", df_maestro["Orquesta"].unique())
    fecha_hoy = st.sidebar.date_input("Fecha", datetime.now())
    
    df_filtrado = df_maestro[
        (df_maestro["Orquesta"] == orquesta_sel) & 
        (df_maestro["Estado"].str.upper() == "ACTIVO")
    ].sort_values(by="NNA").copy()

    if docente_sel == "Selecciona...":
        st.info("👈 Selecciona docente para comenzar")
    else:
        st.subheader(f"Lista {orquesta_sel}")
        
        asistencias = {}
        observaciones = {}

        for i, row in df_filtrado.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 3, 4])
                with col1:
                    st.write(f"**{row['NNA']}**")
                    st.caption(row['Instrumento'])
                with col2:
                    asistencias[row['NNA']] = st.radio(
                        f"Asist_{row['NNA']}", ["P", "FX", "FNX"],
                        horizontal=True, label_visibility="collapsed", key=f"r_{i}"
                    )
                with col3:
                    observaciones[row['NNA']] = st.text_input(
                        "Obs", placeholder="Notas...", label_visibility="collapsed", key=f"o_{i}"
                    )
                st.markdown("---")

        # PASO 1: GUARDAR LOCALMENTE PARA REVISAR
        if st.button("🔍 1. GUARDAR Y REVISAR"):
            resumen = []
            for nombre in asistencias:
                inst = df_filtrado[df_filtrado["NNA"] == nombre]["Instrumento"].values[0]
                resumen.append({
                    "Fecha": fecha_hoy.strftime("%d/%m/%Y"),
                    "Orquesta": orquesta_sel,
                    "Docente": docente_sel,
                    "NNA": nombre,
                    "Instrumento": inst,
                    "V/F": asistencias[nombre],  # Aquí se guarda P, FX o FNX
                    "Actitud": "N/A",            # Columna requerida por tu Excel
                    "Nota": 0,                   # Columna requerida por tu Excel
                    "Observaciones": observaciones[nombre]
                })
            st.session_state.temp_data = pd.DataFrame(resumen)
            st.table(st.session_state.temp_data)

        # PASO 2: ENVIAR A GOOGLE SHEETS
        if "temp_data" in st.session_state:
            if st.button("🚀 2. CONFIRMAR ENVÍO A HISTORIAL"):
                try:
                    # Leemos lo que ya hay en HISTORIAL
                    df_historial = conn.read(worksheet="HISTORIAL", ttl="0")
                    # Unimos lo nuevo
                    df_final = pd.concat([df_historial, st.session_state.temp_data], ignore_index=True)
                    # Subimos todo
                    conn.update(worksheet="HISTORIAL", data=df_final)
                    
                    st.success("✅ ¡Datos enviados con éxito!")
                    st.balloons()
                    del st.session_state.temp_data # Limpiamos para evitar duplicados
                except Exception as e:
                    st.error(f"Error al enviar: {e}")

except Exception as e:
    st.error(f"Error: {e}")
