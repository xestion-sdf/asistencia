import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SDF - Portal Docente", layout="wide")

# --- CSS PARA EL COLOR VERDE SDF ---
st.markdown("""
    <style>
    :root { --primary-color: #28a745; }
    div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] > div:first-child {
        border-color: #28a745 !important;
        background-color: #28a745 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS (LECTURA) ---
ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"
URL_LISTADO = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=320023"
URL_DOCENTES = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=1283708974"

@st.cache_data(ttl=60)
def cargar_datos(url):
    df = pd.read_csv(f"{url}&timestamp={datetime.now().timestamp()}")
    df.columns = df.columns.str.strip()
    return df

# --- NAVEGACIÓN LATERAL ---
st.sidebar.title("🎵 SDF Panel")
menu = st.sidebar.radio(
    "Selecciona una función:",
    ["📋 Pasar Asistencia", "🎻 Evaluación Técnica", "🧠 Evaluación Actitudinal"]
)

try:
    df_maestro = cargar_datos(URL_LISTADO)
    df_docentes = cargar_datos(URL_DOCENTES)
    
    st.sidebar.markdown("---")
    docente_sel = st.sidebar.selectbox("Docente", ["Selecciona..."] + df_docentes.iloc[:,0].dropna().unique().tolist())
    orquesta_sel = st.sidebar.selectbox("Orquesta", df_maestro["Orquesta"].unique())
    fecha_hoy = st.sidebar.date_input("Fecha", datetime.now())

    df_filtrado = df_maestro[
        (df_maestro["Orquesta"] == orquesta_sel) & (df_maestro["Estado"].str.upper() == "ACTIVO")
    ].sort_values(by="NNA").copy()

    if docente_sel == "Selecciona...":
        st.info("👈 Por favor, selecciona tu nombre en el menú lateral para comenzar.")
    
    # ---------------------------------------------------------
    # PÁGINA 1: ASISTENCIA
    # ---------------------------------------------------------
    elif menu == "📋 Pasar Asistencia":
        st.header("Control de Asistencia Diaria")
        asistencias = {}
        for i, row in df_filtrado.iterrows():
            col1, col2 = st.columns([3, 2])
            col1.write(f"**{row['NNA']}**")
            asistencias[row['NNA']] = col2.radio(f"A_{i}", ["P", "FX", "FNX"], horizontal=True, label_visibility="collapsed", key=f"as_{i}")
            st.markdown("---")
        
        if st.button("💾 Guardar Asistencia"):
            st.success("Vista previa generada. ¡Listo para enviar!")
            # Aquí pondrías tu lógica de requests.post para asistencia

    # ---------------------------------------------------------
    # PÁGINA 2: EVALUACIÓN TÉCNICA (Likert)
    # ---------------------------------------------------------
    elif menu == "🎻 Evaluación Técnica":
        st.header("Escala Likert: Desempeño Técnico")
        st.caption("1: Inicial | 5: Avanzado")
        notas = {}
        for i, row in df_filtrado.iterrows():
            col1, col2 = st.columns([3, 3])
            col1.write(f"**{row['NNA']}**")
            notas[row['NNA']] = col2.radio(f"T_{i}", ["1", "2", "3", "4", "5"], horizontal=True, label_visibility="collapsed", key=f"te_{i}", index=2)
            st.markdown("---")

    # ---------------------------------------------------------
    # PÁGINA 3: EVALUACIÓN ACTITUDINAL
    # ---------------------------------------------------------
    elif menu == "🧠 Evaluación Actitudinal":
        st.header("Escala Likert: Actitud y Compromiso")
        actitudes = {}
        for i, row in df_filtrado.iterrows():
            col1, col2 = st.columns([3, 3])
            col1.write(f"**{row['NNA']}**")
            actitudes[row['NNA']] = col2.radio(f"Act_{i}", ["1", "2", "3", "4", "5"], horizontal=True, label_visibility="collapsed", key=f"ac_{i}", index=4)
            st.markdown("---")

except Exception as e:
    st.error(f"Error: {e}")
