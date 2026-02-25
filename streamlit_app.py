import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="SDF - Asistencia y Evaluación", layout="wide")

# CSS para intentar forzar el verde (aunque Streamlit sea rebelde)
st.markdown("""
    <style>
    :root { --primary-color: #28a745 !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] > div:first-child {
        border-color: #28a745 !important;
        background-color: #28a745 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# LECTURA DE DATOS
ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"
URL_LISTADO = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=320023"
URL_DOCENTES = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=1283708974"

@st.cache_data(ttl=60)
def cargar_datos(url):
    url_final = f"{url}&timestamp={datetime.now().timestamp()}"
    df = pd.read_csv(url_final)
    df.columns = df.columns.str.strip()
    return df

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSef94w2FNw2XTqRo9ZRnhURSOJx-5iUqeeVZ5kqqASLiTYF0A/formResponse"

try:
    df_maestro = cargar_datos(URL_LISTADO)
    df_docentes = cargar_datos(URL_DOCENTES)
    
    st.sidebar.header("⚙️ Configuración")
    docente_sel = st.sidebar.selectbox("Docente", ["Selecciona..."] + df_docentes.iloc[:,0].dropna().unique().tolist())
    orquesta_sel = st.sidebar.selectbox("Orquesta", df_maestro["Orquesta"].unique())
    fecha_hoy = st.sidebar.date_input("Fecha de hoy", datetime.now())
    
    df_filtrado = df_maestro[
        (df_maestro["Orquesta"] == orquesta_sel) & 
        (df_maestro["Estado"].str.upper() == "ACTIVO")
    ].sort_values(by="NNA").copy()

    if docente_sel == "Selecciona...":
        st.info("👈 Selecciona tu nombre para comenzar.")
    else:
        st.subheader(f"📋 Control de Clase: {orquesta_sel}")
        
        asistencias = {}
        notas = {}
        actitudes = {}
        observaciones = {}

        # Encabezados de columna para guiar al docente
        h1, h2, h3, h4, h5 = st.columns([2, 2, 2, 2, 2])
        h1.caption("ALUMNO")
        h2.caption("ASISTENCIA")
        h3.caption("EVAL. TÉCNICA (1-5)")
        h4.caption("ACTITUD (1-5)")
        h5.caption("OBSERVACIONES")
        st.markdown("---")

        for i, row in df_filtrado.iterrows():
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 2])
                
                with c1:
                    st.write(f"**{row['NNA']}**")
                    st.caption(row['Instrumento'])
                
                with c2:
                    asistencias[row['NNA']] = st.radio(
                        f"asist_{i}", ["P", "FX", "FNX"],
                        horizontal=True, label_visibility="collapsed", key=f"asist_{i}"
                    )
                
                with c3:
                    # Likert Técnica
                    notas[row['NNA']] = st.radio(
                        f"nota_{i}", ["1", "2", "3", "4", "5"],
                        horizontal=True, label_visibility="collapsed", key=f"nota_{i}", index=2
                    )
                
                with c4:
                    # Likert Actitud
                    actitudes[row['NNA']] = st.radio(
                        f"act_{i}", ["1", "2", "3", "4", "5"],
                        horizontal=True, label_visibility="collapsed", key=f"act_{i}", index=4
                    )
                
                with c5:
                    observaciones[row['NNA']] = st.text_input(
                        "Obs", placeholder="...", label_visibility="collapsed", key=f"obs_{i}"
                    )
                st.markdown("---")

        # PASO 1: REVISIÓN
        if st.button("🔍 1. GUARDAR Y REVISAR"):
            fecha_str = fecha_hoy.strftime("%d/%m/%Y")
            resumen_lista = []
            for nna in asistencias:
                inst = df_filtrado[df_filtrado["NNA"] == nna]["Instrumento"].values[0]
                resumen_lista.append({
                    "Fecha": fecha_str,
                    "Orquesta": orquesta_sel,
                    "Docente": docente_sel,
                    "NNA": nna,
                    "Instrumento": inst,
                    "V/F": asistencias[nna],
                    "Nota": notas[nna],
                    "Actitud": actitudes[nna],
                    "Obs": observaciones[nna]
                })
            st.session_state.datos_eval = resumen_lista
            st.success("✅ Revisión generada. Verifica los datos en la tabla inferior.")
            st.table(pd.DataFrame(resumen_lista))

        # PASO 2: ENVÍO
        if "datos_eval" in st.session_state:
            st.warning("⚠️ Verificado. ¿Deseas enviar estos datos al Historial?")
            if st.button("🚀 2. CONFIRMAR ENVÍO DEFINITIVO"):
                exitos = 0
                with st.spinner("Enviando a Google Sheets..."):
                    for d in st.session_state.datos_eval:
                        form_data = {
                            "entry.883067698": d["Fecha"],
                            "entry.695473946": d["Orquesta"],
                            "entry.252597218": d["Docente"],
                            "entry.1616335440": d["NNA"],
                            "entry.1668643155": d["Instrumento"],
                            "entry.1284516970": d["V/F"],
                            "entry.58216437": d["Obs"],
                            # REEMPLAZA ESTOS CON TUS NUEVOS IDS DEL FORMULARIO:
                            "entry.1111111111": d["Nota"],    # ID para Nota
                            "entry.2222222222": d["Actitud"]  # ID para Actitud
                        }
                        try:
                            requests.post(FORM_URL, data=form_data)
                            exitos += 1
                        except: pass
                
                if exitos > 0:
                    st.success(f"✅ ¡Historial actualizado con {exitos} registros!")
                    st.balloons()
                    del st.session_state.datos_eval
                else:
                    st.error("Hubo un problema al conectar con el servidor.")

except Exception as e:
    st.error(f"Error: {e}")
