import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Control Orquesta SDF", layout="wide")

# URL DIRECTA AL CSV (Sin pasar por conectores)
# He añadido un parámetro extra para saltar la caché de Google
URL_LISTADO = "https://docs.google.com/spreadsheets/d/1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI/export?format=csv&gid=320023"
URL_DOCENTES = "https://docs.google.com/spreadsheets/d/1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI/export?format=csv&gid=485552718"

st.title("🎻 Gestión de Orquestas SDF")

def cargar_datos(url):
    # Añadimos un timestamp a la URL para engañar a Google y que no dé Error 400 por repetición
    url_final = f"{url}&cache={datetime.now().timestamp()}"
    return pd.read_csv(url_final)

try:
    df_maestro = cargar_datos(URL_LISTADO)
    df_docentes = cargar_datos(URL_DOCENTES)
    
    # Limpiar nombres de columnas
    df_maestro.columns = df_maestro.columns.str.strip()
    
    # Selector en la barra lateral
    docente_sel = st.sidebar.selectbox("Docente", df_docentes.iloc[:,0].unique())
    orquesta_sel = st.sidebar.selectbox("Orquesta", df_maestro["Orquesta"].unique())
    
    # Filtro de alumnos
    df_filtrado = df_maestro[(df_maestro["Orquesta"] == orquesta_sel) & (df_maestro["Estado"].str.upper() == "ACTIVO")].copy()
    
    if not df_filtrado.empty:
        st.subheader(f"Lista de {orquesta_sel}")
        # Tabla simple para verificar si cargan los datos
        st.data_editor(
            df_filtrado[["NNA", "Instrumento", "V/F", "Actitud", "Nota", "Observaciones"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("No hay alumnos activos para esta orquesta.")

except Exception as e:
    st.error(f"Fallo crítico: {e}")
    st.info("💡 Si ves 'Error 400', abre tu Excel -> Compartir -> Asegúrate de que diga 'Cualquier persona con el enlace puede leer'.")
