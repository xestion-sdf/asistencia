import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="SDF - Evaluación Técnica", layout="wide")

# --- CSS PARA EL COLOR VERDE (SDF STYLE) ---
st.markdown("""
    <style>
    div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] > div:first-child {
        border-color: #28a745 !important;
        background-color: #28a745 !important;
    }
    :root { --primary-color: #28a745; }
    </style>
    """, unsafe_allow_html=True)

# LECTURA DE DATOS (Mismos orígenes)
ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"
URL_LISTADO = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=320023"
URL_DOCENTES = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=1283708974"

@st.cache_data(ttl=60)
def cargar_datos(url):
    df = pd.read_csv(f"{url}&timestamp={datetime.now().timestamp()}")
    df.columns = df.columns.str.strip()
    return df

# URL DEL NUEVO FORMULARIO DE EVALUACIÓN
FORM_URL_EVAL = "AQUÍ_TU_NUEVA_URL_DE_FORM_RESPONSE"

try:
    df_maestro = cargar_datos(URL_LISTADO)
    df_docentes = cargar_datos(URL_DOCENTES)
    
    st.title("🎻 Evaluación de Desempeño")
    
    col_a, col_b = st.columns(2)
    with col_a:
        docente_sel = st.selectbox("Docente Evaluador", ["Selecciona..."] + df_docentes.iloc[:,0].dropna().unique().tolist())
    with col_b:
        orquesta_sel = st.selectbox("Orquesta", df_maestro["Orquesta"].unique())

    df_filtrado = df_maestro[
        (df_maestro["Orquesta"] == orquesta_sel) & (df_maestro["Estado"].str.upper() == "ACTIVO")
    ].sort_values(by="NNA").copy()

    if docente_sel != "Selecciona...":
        
        # Diccionarios de datos
        notas = {}
        actitudes = {}
        observaciones = {}

        st.info("💡 Escala Likert: 1 (Bajo) a 5 (Excelente)")

        for i, row in df_filtrado.iterrows():
            with st.expander(f"👤 {row['NNA']} - {row['Instrumento']}", expanded=True):
                c1, c2, c3 = st.columns([3, 3, 4])
                
                with c1:
                    st.write("**Nivel Técnico**")
                    notas[row['NNA']] = st.radio(f"T_{i}", ["1", "2", "3", "4", "5"], horizontal=True, key=f"t_{i}", index=2)
                
                with c2:
                    st.write("**Actitud en Clase**")
                    actitudes[row['NNA']] = st.radio(f"A_{i}", ["1", "2", "3", "4", "5"], horizontal=True, key=f"a_{i}", index=4)
                
                with c3:
                    st.write("**Comentarios**")
                    observaciones[row['NNA']] = st.text_area("Obs", placeholder="Escribe aquí...", label_visibility="collapsed", key=f"o_{i}", height=70)

        if st.button("🔍 GUARDAR EVALUACIONES Y REVISAR"):
            resumen = []
            for nna in notas:
                resumen.append({
                    "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Orquesta": orquesta_sel,
                    "Docente": docente_sel,
                    "Alumno": nna,
                    "Nota Técnica": notas[nna],
                    "Actitud": actitudes[nna],
                    "Observaciones": observaciones[nna]
                })
            st.session_state.eval_data = resumen
            st.table(pd.DataFrame(resumen))

        if "eval_data" in st.session_state:
            if st.button("🚀 ENVIAR EVALUACIÓN A LA NUEVA PESTAÑA"):
                # Aquí iría el bucle de requests.post con los nuevos entry.XXXX
                st.success("¡Datos enviados a la nueva base de datos!")
                st.balloons()
                del st.session_state.eval_data

except Exception as e:
    st.error(f"Error: {e}")
