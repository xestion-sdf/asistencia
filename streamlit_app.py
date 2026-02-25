import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SDF - Asistencia Rápida", layout="wide")

# --- ESTILO CSS PARA CAMBIAR ROJO POR VERDE ---
st.markdown("""
    <style>
    /* Cambia el color del círculo seleccionado a verde */
    div[data-testid="stWidgetLabel"] {
        font-weight: bold;
    }
    div[data-basebutton="true"] {
        color: green;
    }
    /* Color verde para el botón de radio seleccionado */
    header, .st-emotion-cache-16idsys p {
        color: black;
    }
    .st-emotion-cache-6q9sum.edgvbvh3 {
        background-color: green;
    }
    /* Selector de radio en verde */
    div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] > div:first-child {
        border-color: #28a745 !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] > div:first-child > div {
        background-color: #28a745 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURACIÓN DE LECTURA (LO QUE FUNCIONA) ---
ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"
URL_LISTADO = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=320023"
URL_DOCENTES = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=485552718"

@st.cache_data(ttl=60)
def cargar_datos(url):
    url_final = f"{url}&cache={datetime.now().timestamp()}"
    df = pd.read_csv(url_final)
    df.columns = df.columns.str.strip()
    return df

try:
    df_maestro = cargar_datos(URL_LISTADO)
    df_docentes = cargar_datos(URL_DOCENTES)
    
    st.sidebar.header("⚙️ Configuración")
    docente_sel = st.sidebar.selectbox("Docente", ["Selecciona..."] + df_docentes.iloc[:,0].dropna().unique().tolist())
    orquesta_sel = st.sidebar.selectbox("Orquesta", df_maestro["Orquesta"].unique())
    fecha_hoy = st.sidebar.date_input("Fecha", datetime.now())
    
    df_filtrado = df_maestro[
        (df_maestro["Orquesta"] == orquesta_sel) & 
        (df_maestro["Estado"].str.upper() == "ACTIVO")
    ].sort_values(by="NNA").copy()

    if docente_sel == "Selecciona...":
        st.info("👈 Selecciona tu nombre en el menú lateral.")
    else:
        st.subheader(f"📋 Pasando asistencia: {orquesta_sel}")
        
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
                        f"asist_{row['NNA']}", 
                        ["P", "FX", "FNX"],
                        horizontal=True, 
                        label_visibility="collapsed", 
                        key=f"r_{i}"
                    )
                with col3:
                    observaciones[row['NNA']] = st.text_input(
                        "Obs", placeholder="Nota/Obs", 
                        label_visibility="collapsed", key=f"t_{i}"
                    )
                st.markdown("---")

        # --- REVISIÓN ANTES DE GUARDAR ---
        if st.button("🔍 REVISAR ASISTENCIA"):
            st.markdown("### 📝 Resumen para revisión")
            resumen = []
            for _, row in df_filtrado.iterrows():
                resumen.append({
                    "Alumno": row['NNA'],
                    "Asistencia": asistencias[row['NNA']],
                    "Observaciones": observaciones[row['NNA']]
                })
            st.table(pd.DataFrame(resumen))
            
            # Aquí pondremos el botón final de envío una vez confirmes que este diseño te gusta
            st.warning("Si todo está correcto, confirma para enviar al Excel.")

except Exception as e:
    st.error(f"Error: {e}")
