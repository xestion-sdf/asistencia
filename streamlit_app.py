import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Control Orquesta SDF", layout="wide", page_icon="🎻")

# ID de tu documento
ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"

# GIDs (Confirmados por ti)
GID_LISTADO = "320023"
GID_DOCENTES = "485552718"

@st.cache_data(ttl=0)
def cargar_pestaña(gid):
    url = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={gid}"
    df = pd.read_csv(url)
    # LIMPIEZA: Quitamos espacios en blanco al principio/final de los textos y nombres de columnas
    df.columns = df.columns.str.strip()
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    return df

st.title("🎻 Control de Asistencia y Evaluación")

try:
    df_maestro = cargar_pestaña(320023)
    df_docentes = cargar_pestaña(1283708974)
    
    # Barra lateral
    st.sidebar.header("⚙️ Configuración")
    
    # Selector de Docente (Columna "Nombre")
    col_nombre_docente = df_docentes.columns[0] # Toma la primera columna sea cual sea su nombre
    lista_docentes = df_docentes[col_nombre_docente].dropna().unique().tolist()
    docente_sel = st.sidebar.selectbox("Docente responsable:", ["Selecciona..."] + lista_docentes)
    
    # Selector de Orquesta
    lista_orquestas = df_maestro["Orquesta"].dropna().unique().tolist()
    orquesta_sel = st.sidebar.selectbox("Selecciona Orquesta:", lista_orquestas)
    
    fecha_hoy = st.sidebar.date_input("Fecha de hoy:", datetime.now())

    # --- FILTRADO ROBUSTO ---
    # Convertimos a mayúsculas para comparar y evitar errores de "Activo" vs "ACTIVO"
    df_maestro["Estado_Upper"] = df_maestro["Estado"].astype(str).str.upper()
    
    mask = (df_maestro["Orquesta"] == orquesta_sel) & (df_maestro["Estado_Upper"] == "ACTIVO")
    df_filtrado = df_maestro[mask].copy()

    if docente_sel == "Selecciona...":
        st.info("👈 Selecciona tu nombre en el menú lateral para cargar los alumnos.")
    
    elif df_filtrado.empty:
        st.warning(f"No hay alumnos con Estado 'ACTIVO' en la orquesta '{orquesta_sel}'.")
        # Mostramos qué hay en la columna Estado para depurar
        with st.expander("Depuración: Ver estados encontrados"):
            st.write("Estados actuales en esta orquesta:", df_maestro[df_maestro["Orquesta"] == orquesta_sel]["Estado"].unique())
            
    else:
        st.subheader(f"📋 Lista: {orquesta_sel} ({len(df_filtrado)} alumnos)")
        
        # Editor de tabla
        df_editado = st.data_editor(
            df_filtrado[["NNA", "Instrumento", "V/F", "Actitud", "Nota", "Observaciones"]],
            column_config={
                "NNA": st.column_config.Column("Alumno", disabled=True),
                "Instrumento": st.column_config.Column("Instrumento", disabled=True),
                "V/F": st.column_config.SelectboxColumn("Asistencia", options=["P", "FX", "FNX"], required=True),
                "Actitud": st.column_config.SelectboxColumn("Actitud", options=["🌟 Excelente", "✅ Bien", "⚠️ Regular", "❌ Mal"]),
                "Nota": st.column_config.NumberInputColumn("Nota (1-5)", min_value=1, max_value=5, step=1),
                "Observaciones": st.column_config.TextColumn("Observaciones", width="large")
            },
            hide_index=True,
            use_container_width=True,
            key="editor_asistencia"
        )

        if st.button("🚀 GUARDAR ASISTENCIA"):
            # Aquí procesaremos el guardado en el siguiente paso
            st.success("Datos listos para ser enviados al Historial.")
            st.dataframe(df_editado)

except Exception as e:
    st.error(f"Se produjo un error: {e}")
    st.info("Revisa que los encabezados del Excel sean: NNA, Orquesta, Instrumento, Estado, V/F, Actitud, Nota, Observaciones")
# FOOTER
st.markdown("---")
st.caption("Sistema de Gestión de Orquestas - SDF 2026")
