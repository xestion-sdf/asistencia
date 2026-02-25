import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="SDF - Asistencia Rápida", layout="wide")

# --- ESTILO CSS PARA CÍRCULOS VERDES ---
st.markdown("""
    <style>
    /* Forzar color verde en los radio buttons seleccionados */
    div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] > div:first-child {
        border-color: #28a745 !important;
        background-color: #28a745 !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] > div:first-child > div {
        background-color: white !important;
        width: 8px;
        height: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURACIÓN DE LECTURA SEGURA ---
ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"
URL_LISTADO = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=320023"
URL_DOCENTES = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=1283708974"

@st.cache_data(ttl=60)
def cargar_datos(url):
    # El timestamp evita que Google nos dé error por repetir la petición
    url_final = f"{url}&cache={datetime.now().timestamp()}"
    df = pd.read_csv(url_final)
    df.columns = df.columns.str.strip()
    return df

# Conector solo para enviar
conn = st.connection("gsheets", type=GSheetsConnection)

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
        st.info("👈 Selecciona tu nombre para cargar la lista.")
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

        # --- SISTEMA DE GUARDADO EN DOS PASOS ---
        if st.button("🔍 1. REVISAR Y PREPARAR ENVÍO"):
            st.session_state.listo_para_enviar = True
            
        if "listo_para_enviar" in st.session_state and st.session_state.listo_para_enviar:
            st.markdown("### 📝 Resumen para confirmación")
            datos_envio = []
            for _, row in df_filtrado.iterrows():
                datos_envio.append({
                    "Fecha": fecha_hoy.strftime("%d/%m/%Y"),
                    "Orquesta": orquesta_sel,
                    "Docente": docente_sel,
                    "NNA": row['NNA'],
                    "Instrumento": row['Instrumento'],
                    "V/F": asistencias[row['NNA']],
                    "Actitud": "✅",
                    "Nota": 0,
                    "Observaciones": observaciones[row['NNA']]
                })
            df_resumen = pd.DataFrame(datos_envio)
            st.table(df_resumen)

            if st.button("🚀 2. CONFIRMAR Y ENVIAR A GOOGLE SHEETS"):
                try:
                    with st.spinner("Guardando en HISTORIAL..."):
                        # Leemos historial actual para añadir debajo
                        df_historial_viejo = conn.read(worksheet="HISTORIAL", ttl="0")
                        df_final = pd.concat([df_historial_viejo, df_resumen], ignore_index=True)
                        conn.update(worksheet="HISTORIAL", data=df_final)
                        
                        st.success("¡Datos guardados con éxito!")
                        st.balloons()
                        st.session_state.listo_para_enviar = False
                except Exception as e_envio:
                    st.error(f"Fallo al enviar: {e_envio}")

except Exception as e:
    st.error(f"Error de carga: {e}")
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
