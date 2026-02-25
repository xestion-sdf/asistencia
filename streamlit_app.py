import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="SDF - Asistencia", layout="wide")

# --- CSS PARA EL COLOR VERDE SDF ---
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

# LECTURA SEGURA (La que te funciona)
ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"
URL_LISTADO = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=320023"
URL_DOCENTES = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=1283708974"

@st.cache_data(ttl=60)
def cargar_datos(url):
    df = pd.read_csv(f"{url}&timestamp={datetime.now().timestamp()}")
    df.columns = df.columns.str.strip()
    return df

# --- CONFIGURACIÓN DEL FORMULARIO (PARA EL ENVÍO) ---
# Sustituye esto por el ID de tu formulario si quieres automatizarlo
FORM_URL = "https://forms.gle/3yyJgntSJ7H1pmhW7/HISTORIAL"

try:
    df_maestro = cargar_datos(URL_LISTADO)
    df_docentes = cargar_datos(URL_DOCENTES)
    
    st.sidebar.header("⚙️ Configuración")
    docente_sel = st.sidebar.selectbox("Docente", ["Selecciona..."] + df_docentes.iloc[:,0].dropna().unique().tolist())
    orquesta_sel = st.sidebar.selectbox("Orquesta", df_maestro["Orquesta"].unique())
    
    df_filtrado = df_maestro[
        (df_maestro["Orquesta"] == orquesta_sel) & 
        (df_maestro["Estado"].str.upper() == "ACTIVO")
    ].sort_values(by="NNA").copy()

    if docente_sel == "Selecciona...":
        st.info("👈 Selecciona tu nombre.")
    else:
        asistencias = {}
        observaciones = {}

        for i, row in df_filtrado.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 3, 4])
                with col1:
                    st.write(f"**{row['NNA']}**")
                with col2:
                    asistencias[row['NNA']] = st.radio(
                        f"r_{i}", ["P", "FX", "FNX"],
                        horizontal=True, label_visibility="collapsed", key=f"r_{i}"
                    )
                with col3:
                    observaciones[row['NNA']] = st.text_input("Obs", label_visibility="collapsed", key=f"o_{i}")
                st.markdown("---")

        if st.button("🚀 GUARDAR ASISTENCIA"):
            # Generamos un CSV para descargar como "Plan B" por si el 400 sigue en Google
            resumen = []
            for nna in asistencias:
                resumen.append({
                    "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Orquesta": orquesta_sel,
                    "Docente": docente_sel,
                    "NNA": nna,
                    "Asistencia": asistencias[nna],
                    "Obs": observaciones[nna]
                })
            df_final = pd.DataFrame(resumen)
            
            st.success("✅ ¡Lista procesada localmente!")
            st.table(df_final)
            
            # Botón de descarga para que NUNCA pierdas el trabajo si Google falla
            csv = df_final.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Backup CSV", csv, "asistencia.csv", "text/csv")

except Exception as e:
    st.error(f"Error: {e}")
