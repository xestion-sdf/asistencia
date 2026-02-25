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

# --- IMPORTANTE: Cambia este GID por el de tu pestaña de respuestas de Google Sheets ---
GID_HISTORIAL = "PON_AQUI_EL_GID_DE_TU_HOJA_DE_RESPUESTAS" 
URL_HISTORIAL = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_HISTORIAL}"

@st.cache_data(ttl=60)
def cargar_datos(url):
    df = pd.read_csv(f"{url}&timestamp={datetime.now().timestamp()}")
    df.columns = df.columns.str.strip()
    return df

FORM_ASISTENCIA = "https://docs.google.com/forms/d/e/1FAIpQLSef94w2FNw2XTqRo9ZRnhURSOJx-5iUqeeVZ5kqqASLiTYF0A/formResponse"
FORM_EVAL_INTEGRAL = "TU_NUEVA_URL_AQUI" 

# --- 3. BARRA LATERAL (NAVEGACIÓN) ---
st.sidebar.title("🎵 SDF Panel")
menu = st.sidebar.radio(
    "Selecciona una función:",
    ["📋 Asistencia Diaria", "🎻 Evaluación Técnica", "🧠 Evaluación Actitudinal", "📊 Consulta de Registros"]
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

    # --- PÁGINA 3: ACTITUDINAL ---
    elif menu == "🧠 Evaluación Actitudinal":
        st.header("Notas Actitudinales")
        st.write("Esta sección se mantiene para reportes específicos.")

    # --- PÁGINA 4: CONSULTA (NUEVA) ---
    elif menu == "📊 Consulta de Registros":
        st.header("Historial de Registros")
        try:
            df_hist = cargar_datos(URL_HISTORIAL)
            tab1, tab2 = st.tabs(["📅 Por Día", "👤 Por Alumno"])
            
            with tab1:
                f_busq = st.date_input("Día a consultar", datetime.now())
                f_str = f_busq.strftime("%d/%m/%Y")
                res_dia = df_hist[df_hist.iloc[:, 1] == f_str] # Ajusta el índice de columna de fecha
                if not res_dia.empty:
                    st.dataframe(res_dia, use_container_width=True)
                else:
                    st.info("No hay registros en esta fecha.")
            
            with tab2:
                al_lista = df_maestro[df_maestro["Orquesta"] == orquesta_sel]["NNA"].unique()
                al_busq = st.selectbox("Selecciona Alumno", al_lista)
                res_al = df_hist[df_hist.iloc[:, 4] == al_busq] # Ajusta el índice de columna de NNA
                if not res_al.empty:
                    st.dataframe(res_al, use_container_width=True)
                else:
                    st.info("Sin registros para este alumno.")
        except:
            st.error("Aún no se puede acceder al historial. Verifica el GID.")

except Exception as e:
    st.error(f"Error: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("SDF - Sistema de Gestión 2026")
