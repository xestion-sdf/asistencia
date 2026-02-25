import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="SDF - Control de Asistencia", layout="wide")

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

# --- CONFIGURACIÓN DE LECTURA ---
ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"
URL_LISTADO = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=320023"
URL_DOCENTES = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=1283708974"

@st.cache_data(ttl=60)
def cargar_datos(url):
    url_final = f"{url}&timestamp={datetime.now().timestamp()}"
    df = pd.read_csv(url_final)
    df.columns = df.columns.str.strip()
    return df

# URL de tu Google Form
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSef94w2FNw2XTqRo9ZRnhURSOJx-5iUqeeVZ5kqqASLiTYF0A/formResponse"

try:
    df_maestro = cargar_datos(URL_LISTADO)
    df_docentes = cargar_datos(URL_DOCENTES)
    
    st.sidebar.header("⚙️ Configuración")
    docente_sel = st.sidebar.selectbox("Docente", ["Selecciona..."] + df_docentes.iloc[:,0].dropna().unique().tolist())
    orquesta_sel = st.sidebar.selectbox("Orquesta", df_maestro["Orquesta"].unique())
    fecha_hoy = st.sidebar.date_input("Fecha de clase", datetime.now())
    
    df_filtrado = df_maestro[
        (df_maestro["Orquesta"] == orquesta_sel) & 
        (df_maestro["Estado"].str.upper() == "ACTIVO")
    ].sort_values(by="NNA").copy()

    if docente_sel == "Selecciona...":
        st.info("👈 Selecciona tu nombre para comenzar.")
    else:
        st.subheader(f"📋 Lista: {orquesta_sel}")
        
        asistencias = {}
        observaciones = {}

        for i, row in df_filtrado.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 3, 4])
                with col1:
                    st.write(f"**{row['NNA']}**")
                    st.caption(f"🎻 {row['Instrumento']}")
                with col2:
                    asistencias[row['NNA']] = st.radio(
                        f"asist_{row['NNA']}", ["P", "FX", "FNX"],
                        horizontal=True, label_visibility="collapsed", key=f"r_{i}"
                    )
                with col3:
                    observaciones[row['NNA']] = st.text_input(
                        "Obs", placeholder="Nota/Obs", 
                        label_visibility="collapsed", key=f"t_{i}"
                    )
                st.markdown("---")

        # --- PASO 1: GUARDAR Y REVISAR ---
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
                    "Obs": observaciones[nna]
                })
            
            # Guardamos en la memoria de la sesión (session_state)
            st.session_state.datos_a_enviar = resumen_lista
            st.success("✅ Datos guardados temporalmente. Revísalos abajo.")
            st.table(pd.DataFrame(resumen_lista))

        # --- PASO 2: ENVIAR DEFINITIVO (Solo aparece si ya se guardó) ---
        if "datos_a_enviar" in st.session_state:
            st.warning("⚠️ Revisa la tabla superior. Si es correcta, pulsa el botón de enviar.")
            if st.button("🚀 2. CONFIRMAR Y ENVIAR AL HISTORIAL"):
                exitos = 0
                total = len(st.session_state.datos_a_enviar)
                
                with st.spinner("Enviando registros..."):
                    for dato in st.session_state.datos_a_enviar:
                        form_data = {
                            "entry.883067698": dato["Fecha"],
                            "entry.695473946": dato["Orquesta"],
                            "entry.252597218": dato["Docente"],
                            "entry.1616335440": dato["NNA"],
                            "entry.1668643155": dato["Instrumento"],
                            "entry.1284516970": dato["V/F"],
                            "entry.58216437": dato["Obs"]
                        }
                        try:
                            response = requests.post(FORM_URL, data=form_data)
                            if response.status_code == 200:
                                exitos += 1
                        except:
                            pass
                
                if exitos == total:
                    st.success(f"✅ ¡Éxito! Se enviaron los {exitos} registros.")
                    st.balloons()
                    # Borramos de la memoria para que no se envíe dos veces por error
                    del st.session_state.datos_a_enviar
                else:
                    st.error(f"Error: Solo se enviaron {exitos} de {total}. Revisa la conexión.")

except Exception as e:
    st.error(f"Error: {e}")
