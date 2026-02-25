import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="SDF - Asistencia Rápida", layout="wide")

# --- LO QUE FUNCIONA (SE MANTIENE IGUAL) ---
ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"
URL_LISTADO = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=320023"
URL_DOCENTES = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=1283708974"

@st.cache_data(ttl=300)
def cargar_datos(url):
    # Mantenemos el truco del timestamp para evitar el Error 400
    df = pd.read_csv(f"{url}&timestamp={datetime.now().hour}")
    df.columns = df.columns.str.strip()
    return df

# Conector solo para enviar datos (Escritura)
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df_maestro = cargar_datos(URL_LISTADO)
    df_docentes = cargar_datos(URL_DOCENTES)
    
    st.sidebar.header("⚙️ Configuración")
    docente_sel = st.sidebar.selectbox("Docente", ["Selecciona..."] + df_docentes.iloc[:,0].dropna().unique().tolist())
    orquesta_sel = st.sidebar.selectbox("Orquesta", df_maestro["Orquesta"].unique())
    fecha_hoy = st.sidebar.date_input("Fecha de clase", datetime.now())
    
    # Filtro idéntico al anterior
    df_filtrado = df_maestro[
        (df_maestro["Orquesta"] == orquesta_sel) & 
        (df_maestro["Estado"].str.upper() == "ACTIVO")
    ].sort_values(by="NNA").copy()

    if docente_sel == "Selecciona...":
        st.info("👈 Selecciona docente")
    else:
        st.subheader(f"Lista {orquesta_sel}")
        
        asistencias = {}
        observaciones = {}

        # Mantenemos las filas rápidas que te gustaron
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

        # --- EL ENVÍO (LO NUEVO) ---
        if st.button("🚀 GUARDAR EN GOOGLE SHEETS"):
            with st.spinner("Enviando..."):
                # Preparamos los datos con el formato de tu HISTORIAL
                nuevos_registros = []
                for _, row in df_filtrado.iterrows():
                    nuevos_registros.append({
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
                
                df_nuevo = pd.DataFrame(nuevos_registros)
                
                # Leemos el historial actual y añadimos lo nuevo
                df_hist_actual = conn.read(worksheet="HISTORIAL", ttl="0")
                df_final = pd.concat([df_hist_actual, df_nuevo], ignore_index=True)
                
                # Escribimos de vuelta
                conn.update(worksheet="HISTORIAL", data=df_final)
                
                st.success("¡Guardado con éxito en la pestaña HISTORIAL!")
                st.balloons()

except Exception as e:
    st.error(f"Error: {e}")
