import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="SDF - Portal Docente", layout="wide")

st.markdown("""
    <style>
    :root { --primary-color: #28a745 !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] > div:first-child {
        border-color: #28a745 !important;
        background-color: #28a745 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CARGA DE DATOS ---
ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"
URL_LISTADO = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=320023"
URL_DOCENTES = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=1283708974"

@st.cache_data(ttl=60)
def cargar_datos(url):
    df = pd.read_csv(f"{url}&timestamp={datetime.now().timestamp()}")
    df.columns = df.columns.str.strip()
    return df

# URLs de Google Forms (Actualiza estas con tus nuevos formularios cuando los tengas)
FORM_ASISTENCIA = "https://docs.google.com/forms/d/e/1FAIpQLSef94w2FNw2XTqRo9ZRnhURSOJx-5iUqeeVZ5kqqASLiTYF0A/formResponse"
FORM_EVAL_INTEGRAL = "TU_NUEVA_URL_AQUI" 

# --- 3. BARRA LATERAL (NAVEGACIÓN) ---
st.sidebar.title("🎵 SDF Panel")
menu = st.sidebar.radio(
    "Selecciona una función:",
    ["📋 Asistencia Diaria", "🎻 Evaluación Técnica", "🧠 Evaluación Actitudinal"]
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
    
    # --- PÁGINA 1: ASISTENCIA ---
    elif menu == "📋 Asistencia Diaria":
        st.header(f"Asistencia - {orquesta_sel}")
        asistencias = {}
        observaciones = {}
        for i, row in df_filtrado.iterrows():
            c1, c2, c3 = st.columns([3, 2, 4])
            c1.write(f"**{row['NNA']}**")
            asistencias[row['NNA']] = c2.radio(f"as_{i}", ["P", "FX", "FNX"], horizontal=True, label_visibility="collapsed", key=f"as_{i}")
            observaciones[row['NNA']] = c3.text_input("Obs", placeholder="Nota", label_visibility="collapsed", key=f"ob_{i}")
            st.markdown("---")
        
        if st.button("🔍 GUARDAR Y REVISAR ASISTENCIA"):
            resumen_as = [{"Fecha": fecha_hoy.strftime("%d/%m/%Y"), "NNA": n, "Estado": asistencias[n], "Obs": observaciones[n]} for n in asistencias]
            st.session_state.temp_asistencia = resumen_as
            st.table(pd.DataFrame(resumen_as))

    # --- PÁGINA 2: EVALUACIÓN TÉCNICA (MULTI-LIKERT) ---
    elif menu == "🎻 Evaluación Técnica":
        st.header("Evaluación Integral de Desempeño")
        st.info("Califica del 1 al 5 cada indicador")
        eval_completa = {}
        for i, row in df_filtrado.iterrows():
            with st.expander(f"👤 {row['NNA']} ({row['Instrumento']})"):
                c1, c2 = st.columns(2)
                with c1:
                    nota_tec = st.radio(f"Técnica - {row['NNA']}", ["1","2","3","4","5"], horizontal=True, key=f"tec_{i}", index=2)
                    nota_lec = st.radio(f"Lectura - {row['NNA']}", ["1","2","3","4","5"], horizontal=True, key=f"lec_{i}", index=2)
                with c2:
                    nota_par = st.radio(f"Participación - {row['NNA']}", ["1","2","3","4","5"], horizontal=True, key=f"par_{i}", index=4)
                    nota_mat = st.radio(f"Responsabilidad - {row['NNA']}", ["1","2","3","4","5"], horizontal=True, key=f"mat_{i}", index=4)
                eval_completa[row['NNA']] = {"T": nota_tec, "L": nota_lec, "P": nota_par, "R": nota_mat}

        if st.button("🔍 GUARDAR Y REVISAR EVALUACIÓN"):
            resumen_ev = [{"NNA": n, "Téc": v["T"], "Lec": v["L"], "Par": v["P"], "Res": v["R"]} for n, v in eval_completa.items()]
            st.session_state.temp_eval = resumen_ev
            st.table(pd.DataFrame(resumen_ev))

    # --- PÁGINA 3: ACTITUDINAL (PROVISIONAL) ---
    elif menu == "🧠 Evaluación Actitudinal":
        st.header("Notas Actitudinales")
        st.write("Esta sección se puede usar para reportes de conducta específicos.")

# --- CIERRE DEL BLOQUE PRINCIPAL ---
except Exception as e:
    st.error(f"Hubo un error al cargar los datos: {e}")

# --- PIE DE PÁGINA ---
st.sidebar.markdown("---")
st.sidebar.caption("SDF - Sistema de Gestión 2026")
