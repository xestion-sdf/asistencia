import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="SDF - Control de Asistencia", layout="wide")

# --- CSS PARA EL COLOR VERDE SDF EN LOS BOTONES ---
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

# --- CONFIGURACIÓN DE LECTURA (LO QUE FUNCIONA) ---
ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"
URL_LISTADO = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=320023"
URL_DOCENTES = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=1283708974"

@st.cache_data(ttl=60)
def cargar_datos(url):
    # El timestamp evita errores de caché de Google
    url_final = f"{url}&timestamp={datetime.now().timestamp()}"
    df = pd.read_csv(url_final)
    df.columns = df.columns.str.strip()
    return df

# --- CONFIGURACIÓN DE ENVÍO (GOOGLE FORM) ---
# Hemos extraído los IDs de tu enlace
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSef94w2FNw2XTqRo9ZRnhURSOJx-5iUqeeVZ5kqqASLiTYF0A/formResponse"

try:
    df_maestro = cargar_datos(URL_LISTADO)
    df_docentes = cargar_datos(URL_DOCENTES)
    
    st.sidebar.header("⚙️ Configuración")
    docente_sel = st.sidebar.selectbox("Docente", ["Selecciona..."] + df_docentes.iloc[:,0].dropna().unique().tolist())
    orquesta_sel = st.sidebar.selectbox("Orquesta", df_maestro["Orquesta"].unique())
    fecha_hoy = st.sidebar.date_input("Fecha de clase", datetime.now())
    
    # Filtrar alumnos activos
    df_filtrado = df_maestro[
        (df_maestro["Orquesta"] == orquesta_sel) & 
        (df_maestro["Estado"].str.upper() == "ACTIVO")
    ].sort_values(by="NNA").copy()

    if docente_sel == "Selecciona...":
        st.info("👈 Por favor, selecciona tu nombre en el menú lateral.")
    else:
        st.subheader(f"📋 Lista: {orquesta_sel}")
        
        asistencias = {}
        observaciones = {}

        # Generar filas de alumnos
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

        # BOTÓN DE ENVÍO
        if st.button("🚀 ENVIAR ASISTENCIA A GOOGLE SHEETS"):
            fecha_str = fecha_hoy.strftime("%d/%m/%Y")
            exitos = 0
            total = len(df_filtrado)
            
            with st.spinner(f"Enviando {total} registros..."):
                for nna in asistencias:
                    # Buscamos el instrumento correspondiente
                    inst = df_filtrado[df_filtrado["NNA"] == nna]["Instrumento"].values[0]
                    
                    # Mapeo exacto según tu enlace de formulario
                    form_data = {
                        "entry.883067698": fecha_str,
                        "entry.695473946": orquesta_sel,
                        "entry.252597218": docente_sel,
                        "entry.1616335440": nna,
                        "entry.1668643155": inst,
                        "entry.1284516970": asistencias[nna],
                        "entry.58216437": observaciones[nna]
                    }
                    
                    try:
                        # Enviamos a Google Forms (truco para evitar Error 400)
                        response = requests.post(FORM_URL, data=form_data)
                        if response.status_code == 200:
                            exitos += 1
                    except:
                        pass
            
            if exitos == total:
                st.success(f"✅ ¡Todo guardado! Se han enviado los {exitos} alumnos correctamente.")
                st.balloons()
            elif exitos > 0:
                st.warning(f"⚠️ Se enviaron {exitos} de {total} registros. Revisa la conexión.")
            else:
                st.error("❌ No se pudo enviar nada. Verifica la conexión a internet.")

except Exception as e:
    st.error(f"Error en la aplicación: {e}")
