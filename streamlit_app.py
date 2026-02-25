import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SDF - Portal Docente", layout="wide")

# --- CSS PARA FORZAR VERDE SDF ---
st.markdown("""
    <style>
    :root { --primary-color: #28a745 !important; }
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

# --- CONFIGURACIÓN DE FORMULARIO ASISTENCIA ---
FORM_ASISTENCIA = "https://docs.google.com/forms/d/e/1FAIpQLSef94w2FNw2XTqRo9ZRnhURSOJx-5iUqeeVZ5kqqASLiTYF0A/formResponse"

# --- NAVEGACIÓN LATERAL ---
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
    
    # ---------------------------------------------------------
    # PÁGINA 1: ASISTENCIA
    # ---------------------------------------------------------
    elif menu == "📋 Asistencia Diaria":
        st.header(f"Control de Asistencia - {orquesta_sel}")
        asistencias = {}
        observaciones = {}

        for i, row in df_filtrado.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 4])
                col1.write(f"**{row['NNA']}**")
                asistencias[row['NNA']] = col2.radio(f"as_{i}", ["P", "FX", "FNX"], horizontal=True, label_visibility="collapsed", key=f"as_{i}")
                observaciones[row['NNA']] = col3.text_input("Obs", placeholder="Nota opcional", label_visibility="collapsed", key=f"ob_{i}")
                st.markdown("---")
        
        if st.button("🔍 1. GUARDAR Y REVISAR ASISTENCIA"):
            fecha_str = fecha_hoy.strftime("%d/%m/%Y")
            resumen = []
            for nna in asistencias:
                resumen.append({
                    "Fecha": fecha_str, 
                    "Orquesta": orquesta_sel, 
                    "Docente": docente_sel,
                    "NNA": nna, 
                    "Asistencia": asistencias[nna], 
                    "Observaciones": observaciones[nna]
                })
            st.session_state.temp_asistencia = resumen
            st.success("✅ Vista previa generada. Revisa la tabla abajo.")
            st.table(pd.DataFrame(resumen))

        if "temp_asistencia" in st.session_state:
            if st.button("🚀 2. CONFIRMAR ENVÍO DE ASISTENCIA"):
                exitos = 0
                with st.spinner("Enviando..."):
                    for d in st.session_state.temp_asistencia:
                        inst = df_filtrado[df_filtrado["NNA"] == d["NNA"]]["Instrumento"].values[0]
                        # Mapeo corregido sin saltos de línea peligrosos
                        data = {
                            "entry.883067698": d["Fecha"],
                            "entry.695473946": d["Orquesta"],
                            "entry.252597218": d["Docente"],
                            "entry.1616335440": d["NNA"],
                            "entry.1668643155": inst,
                            "entry.1284516970": d["Asistencia"],
                            "entry.58216437": d["Observaciones"]
                        }
                        try:
                            r = requests.post(FORM_ASISTENCIA, data=data)
                            if r.status_code == 200: exitos += 1
                        except: pass
                st.success(f"✅ ¡Enviado! ({exitos} alumnos)")
                del st.session_state.temp_asistencia

    # ---------------------------------------------------------
    # PÁGINA 2 Y 3: Mismo esquema para Evaluación (Estructura base)
    # ---------------------------------------------------------
    elif menu == "🎻 Evaluación Técnica":
        st.header("Evaluación Técnica (Escala 1-5)")
        # Lógica similar para Técnica...
        st.info("Pestaña en desarrollo: Configura el nuevo formulario para activar el envío.")

# --- DENTRO DE LA PESTAÑA DE EVALUACIÓN ---
elif menu == "🎻 Evaluación Técnica":
    st.header("Evaluación Integral de Desempeño")
    st.info("Despliega cada alumno para calificar los 4 indicadores (1: Inicial - 5: Excelente)")
    
    # Diccionarios para guardar las 4 notas por alumno
    eval_completa = {}

    for i, row in df_filtrado.iterrows():
        # Usamos un expansor para que la lista sea scannable
        with st.expander(f"👤 {row['NNA']} ({row['Instrumento']})"):
            c1, c2 = st.columns(2)
            
            with c1:
                nota_tec = st.radio(f"Técnica - {row['NNA']}", ["1", "2", "3", "4", "5"], 
                                    horizontal=True, key=f"tec_{i}", index=2)
                nota_lec = st.radio(f"Lectura - {row['NNA']}", ["1", "2", "3", "4", "5"], 
                                    horizontal=True, key=f"lec_{i}", index=2)
            
            with c2:
                nota_par = st.radio(f"Participación - {row['NNA']}", ["1", "2", "3", "4", "5"], 
                                    horizontal=True, key=f"par_{i}", index=4)
                nota_mat = st.radio(f"Responsabilidad - {row['NNA']}", ["1", "2", "3", "4", "5"], 
                                    horizontal=True, key=f"mat_{i}", index=4)
            
            eval_completa[row['NNA']] = {
                "Tecnica": nota_tec,
                "Lectura": nota_lec,
                "Participacion": nota_par,
                "Responsabilidad": nota_mat
            }

    if st.button("🔍 GUARDAR EVALUACIÓN COMPLETA"):
        resumen_eval = []
        for nna, valores in eval_completa.items():
            resumen_eval.append({
                "NNA": nna,
                "Téc": valores["Tecnica"],
                "Lec": valores["Lectura"],
                "Par": valores["Participacion"],
                "Res": valores["Responsabilidad"]
            })
        st.session_state.temp_eval = resumen_eval
        st.table(pd.DataFrame(resumen_eval))

except Exception as e:
    st.error(f"Error: {e}")
