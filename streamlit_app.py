import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Control Orquesta", layout="wide")
st.title("🎻 Control de Asistencia y Evaluación")

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Leemos la pestaña LISTADO
    df = conn.read(worksheet="LISTADO", ttl="0")
    # Leemos la pestaña DOCENTES
    df_docentes = conn.read(worksheet="DOCENTES", ttl="0")
    
    # Barra lateral
    st.sidebar.header("Configuración")
    docente_sel = st.sidebar.selectbox("Docente", options=["Selecciona..."] + df_docentes["Nombre"].tolist())
    orquesta_sel = st.sidebar.selectbox("Selecciona Orquesta", df["Orquesta"].dropna().unique())
    fecha_hoy = st.sidebar.date_input("Fecha", datetime.now())

    # Filtrado
    df_filtrado = df[(df["Orquesta"] == orquesta_sel) & (df["Estado"] == "ACTIVO")].copy()

    if docente_sel == "Selecciona...":
        st.warning("👈 Por favor, selecciona un docente en la barra lateral.")
    else:
        st.subheader(f"Lista: {orquesta_sel}")
        df_editado = st.data_editor(
            df_filtrado[["NNA", "Instrumento", "V/F", "Actitud", "Nota", "Observaciones"]],
            hide_index=True,
            use_container_width=True
        )
        
        if st.button("🚀 Guardar"):
            st.success("¡Conexión verificada! (Falta configurar el guardado final)")

except Exception as e:
    st.error(f"Error al conectar: {e}")
