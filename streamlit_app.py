import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SDF - Asistencia Rápida", layout="wide")

# --- MANTENEMOS LO QUE FUNCIONA (LECTURA SEGURA) ---
ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"
URL_LISTADO = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=320023"
URL_DOCENTES = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=1283708974"

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
        st.info("👈 Selecciona tu nombre para empezar.")
    else:
        st.subheader(f"📋 Lista: {orquesta_sel}")
        
        # Estilo para resaltar la P en verde (usando Markdown simple en la etiqueta)
        st.markdown("""<style> div[data-testid="stMarkdownContainer"] p { font-size: 14px; } </style>""", unsafe_allow_html=True)

        asistencias = {}
        observaciones = {}

        for i, row in df_filtrado.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 3, 4])
                with col1:
                    st.write(f"**{row['NNA']}**")
                    st.caption(f"🎻 {row['Instrumento']}")
                with col2:
                    # No podemos poner color directo al botón, pero podemos avisar visualmente
                    asistencias[row['NNA']] = st.radio(
                        f"asist_{row['NNA']}", 
                        ["P", "FX", "FNX"],
                        horizontal=True, 
                        label_visibility="collapsed", 
                        key=f"r_{i}"
                    )
                    if asistencias[row['NNA']] == "P":
                        st.markdown("<span style='color:green; font-weight:bold; font-size:12px;'>✅ PRESENTE</span>", unsafe_allow_html=True)
                
                with col3:
                    observaciones[row['NNA']] = st.text_input(
                        "Obs", placeholder="Nota/Obs", 
                        label_visibility="collapsed", key=f"t_{i}"
                    )
                st.markdown("---")

        # --- PASO 1: REVISAR ---
        if st.button("🔍 1. REVISAR LISTADO"):
            resumen = []
            for _, row in df_filtrado.iterrows():
                resumen.append({
                    "Fecha": fecha_hoy.strftime("%d/%m/%Y"),
                    "Docente": docente_sel,
                    "NNA": row['NNA'],
                    "Asistencia": asistencias[row['NNA']],
                    "Obs": observaciones[row['NNA']]
                })
            df_resumen = pd.DataFrame(resumen)
            
            st.warning("⚠️ Revisa los datos aquí debajo. Si son correctos, usa el botón de enviar que aparecerá al final.")
            st.table(df_resumen)
            
            # --- PASO 2: ENVIAR (Solo aparece tras revisar) ---
            # Nota: Para evitar el error 400 al escribir, usaremos un método alternativo más adelante si este falla.
            if st.download_button(
                label="📥 2. DESCARGAR COPIA (Opcional)",
                data=df_resumen.to_csv(index=False).encode('utf-8'),
                file_name=f"asistencia_{orquesta_sel}_{fecha_hoy}.csv",
                mime='text/csv',
            ):
                st.info("Copia guardada.")

        st.info("💡 Para enviar a Google Sheets sin Error 400, asegúrate de que la pestaña HISTORIAL existe y es pública.")

except Exception as e:
    st.error(f"Error: {e}")
