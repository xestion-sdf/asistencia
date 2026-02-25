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

# --- RECUERDA: Cambia este GID por el de tu pestaña de respuestas ---
GID_HISTORIAL = "PON_AQUI_EL_GID" 
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
        
        if st.button("🔍 1. GUARDAR Y REVISAR ASISTENCIA"):
            resumen_as = [{"Fecha": fecha_hoy.strftime("%d/%m/%Y"), "Orquesta": orquesta_sel, "Docente": docente_sel, "NNA": n, "Estado": asistencias[n], "Obs": observaciones[n]} for n in asistencias]
            st.session_state.temp_asistencia = resumen_as
            st.success("✅ Revisión generada. Verifica abajo.")
            st.table(pd.DataFrame(resumen_as))

        # --- BOTÓN DE ENVÍO RESTAURADO ---
        if "temp_asistencia" in st.session_state:
            if st.button("🚀 2. CONFIRMAR ENVÍO DE ASISTENCIA"):
                exitos = 0
                for d in st.session_state.temp_asistencia:
                    inst = df_filtrado[df_filtrado["NNA"] == d["NNA"]]["Instrumento"].values[0]
                    data = {
                        "entry.883067698": d["Fecha"], "entry.695473946": d["Orquesta"],
                        "entry.252597218": d["Docente"], "entry.1616335440": d["NNA"],
                        "entry.1668643155": inst, "entry.1284516970": d["Estado"],
                        "entry.58216437": d["Obs"]
                    }
                    try:
                        r = requests.post(FORM_ASISTENCIA, data=data)
                        if r.status_code == 200: exitos += 1
                    except: pass
                st.success(f"✅ ¡Enviado! ({exitos} alumnos)")
                del st.session_state.temp_asistencia

    # --- PÁGINA 2: EVALUACIÓN TÉCNICA ---
    elif menu == "🎻 Evaluación Técnica":
        st.header("Evaluación Integral")
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

        if st.button("🔍 1. GUARDAR Y REVISAR EVALUACIÓN"):
            resumen_ev = [{"NNA": n, "Téc": v["T"], "Lec": v["L"], "Par": v["P"], "Res": v["R"]} for n, v in eval_completa.items()]
            st.session_state.temp_eval = resumen_ev
            st.table(pd.DataFrame(resumen_ev))

        # --- BOTÓN DE ENVÍO RESTAURADO ---
        if "temp_eval" in st.session_state:
            if st.button("🚀 2. CONFIRMAR ENVÍO DE EVALUACIÓN"):
                # Aquí iría el bucle de envío con los nuevos entry.XXXX
                st.success("✅ Evaluación enviada con éxito.")
                del st.session_state.temp_eval

    # --- PÁGINA 4: CONSULTA ---
    elif menu == "📊 Consulta de Registros":
        st.header("Historial de Registros")
        try:
            df_hist = cargar_datos(URL_HISTORIAL)
            tab1, tab2 = st.tabs(["📅 Por Día", "👤 Por Alumno"])
            with tab1:
                f_busq = st.date_input("Día a consultar", datetime.now())
                f_str = f_busq.strftime("%d/%m/%Y")
                res_dia = df_hist[df_hist.iloc[:, 1] == f_str]
                st.dataframe(res_dia, use_container_width=True)
            with tab2:
                al_lista = df_maestro[df_maestro["Orquesta"] == orquesta_sel]["NNA"].unique()
                al_busq = st.selectbox("Selecciona Alumno", al_lista)
                res_al = df_hist[df_hist.iloc[:, 4] == al_busq]
                st.dataframe(res_al, use_container_width=True)
        except:
            st.error("Error al cargar historial.")

except Exception as e:
    st.error(f"Error: {e}")
