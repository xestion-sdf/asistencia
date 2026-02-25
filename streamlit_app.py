import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Control Orquesta SDF", layout="wide", page_icon="🎻")

# ID de tu documento
ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"
GID_LISTADO = "320023"
GID_DOCENTES = "485552718"

@st.cache_data(ttl=0)
def cargar_pestaña(gid):
    url = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={gid}"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    # Limpiamos solo si son strings
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    return df

st.title("🎻 Control de Asistencia y Evaluación")

try:
    df_maestro = cargar_pestaña(GID_LISTADO)
    df_docentes = cargar_pestaña(GID_DOCENTES)
    
    st.sidebar.header("⚙️ Configuración")
    
    col_nombre_docente = df_docentes.columns[0]
    lista_docentes = df_docentes[col_nombre_docente].dropna().unique().tolist()
    docente_sel = st.sidebar.selectbox("Docente responsable:", ["Selecciona..."] + lista_docentes)
    
    lista_orquestas = df_maestro["Orquesta"].dropna().unique().tolist()
    orquesta_sel = st.sidebar.selectbox("Selecciona Orquesta:", lista_orquestas)
    
    fecha_hoy = st.sidebar.date_input("Fecha de hoy:", datetime.now())

    # FILTRADO
    df_maestro["Estado_Upper"] = df_maestro["Estado"].astype(str).str.upper()
    mask = (df_maestro["Orquesta"] == orquesta_sel) & (df_maestro["Estado_Upper"] == "ACTIVO")
    df_filtrado = df_maestro[mask].copy()

    if docente_sel == "Selecciona...":
        st.info("👈 Selecciona tu nombre en el menú lateral.")
    
    elif df_filtrado.empty:
        st.warning(f"No hay alumnos con Estado 'ACTIVO' en la orquesta '{orquesta_sel}'.")
    else:
        st.subheader(f"📋 Lista: {orquesta_sel} ({len(df_filtrado)} alumnos)")
        
        # TABLA EDITABLE CORREGIDA (Sin NumberInputColumn)
        df_editado = st.data_editor(
            df_filtrado[["NNA", "Instrumento", "V/F", "Actitud", "Nota", "Observaciones"]],
            column_config={
                "NNA": st.column_config.Column("Alumno", disabled=True),
                "Instrumento": st.column_config.Column("Instrumento", disabled=True),
                "V/F": st.column_config.SelectboxColumn("Asistencia", options=["P", "FX", "FNX"], required=True),
                "Actitud": st.column_config.SelectboxColumn("Actitud", options=["🌟 Excelente", "✅ Bien", "⚠️ Regular", "❌ Mal"]),
                # Usamos Column genérico para la Nota para evitar el error de versión
                "Nota": st.column_config.Column("Nota (1-5)"),
                "Observaciones": st.column_config.TextColumn("Observaciones", width="large")
            },
            hide_index=True,
            use_container_width=True,
            key="editor_asistencia"
        )

        if st.button("🚀 GUARDAR ASISTENCIA"):
            st.success("¡Datos capturados correctamente!")
            st.dataframe(df_editado)

except Exception as e:
    st.error(f"Se produjo un error: {e}")
