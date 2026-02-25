import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Control Orquesta SDF", layout="wide", page_icon="🎻")

ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"
GID_LISTADO = "320023"
GID_DOCENTES = "485552718"

@st.cache_data(ttl=0)
def cargar_pestaña(gid):
    url = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={gid}"
    # Forzamos que NNA e Instrumento sean texto para evitar errores si hay celdas raras
    df = pd.read_csv(url, storage_options={"User-Agent": "Mozilla/5.0"})
    df.columns = df.columns.str.strip()
    
    # --- SOLUCIÓN AL ERROR: Asegurar que las columnas editables tengan el tipo correcto ---
    if "Observaciones" in df.columns:
        df["Observaciones"] = df["Observaciones"].astype(str).replace("nan", "")
    if "Nota" in df.columns:
        # Convertimos a numérico, si falla ponemos 0
        df["Nota"] = pd.to_numeric(df["Nota"], errors='coerce').fillna(0).astype(int)
    
    return df

st.title("🎻 Control de Asistencia y Evaluación")

try:
    df_maestro = cargar_pestaña(GID_LISTADO)
    df_docentes = cargar_pestaña(GID_DOCENTES)
    
    # Barra lateral
    st.sidebar.header("⚙️ Configuración")
    
    col_nombre_docente = df_docentes.columns[0]
    lista_docentes = df_docentes[col_nombre_docente].dropna().unique().tolist()
    docente_sel = st.sidebar.selectbox("Docente responsable:", ["Selecciona..."] + lista_docentes)
    
    lista_orquestas = df_maestro["Orquesta"].dropna().unique().tolist()
    orquesta_sel = st.sidebar.selectbox("Selecciona Orquesta:", lista_orquestas)
    
    fecha_hoy = st.sidebar.date_input("Fecha de hoy:", datetime.now())

    # FILTRADO
    df_maestro["Estado_Limpiado"] = df_maestro["Estado"].astype(str).str.strip().str.upper()
    mask = (df_maestro["Orquesta"] == orquesta_sel) & (df_maestro["Estado_Limpiado"] == "ACTIVO")
    df_filtrado = df_maestro[mask].copy()

    if docente_sel == "Selecciona...":
        st.info("👈 Selecciona tu nombre en el menú lateral.")
    elif df_filtrado.empty:
        st.warning(f"No hay alumnos con Estado 'ACTIVO' en la orquesta '{orquesta_sel}'.")
    else:
        st.subheader(f"📋 Lista: {orquesta_sel} ({len(df_filtrado)} alumnos)")
        
        # TABLA EDITABLE BLINDADA
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
            key="editor_v3"
        )

        if st.button("🚀 GUARDAR ASISTENCIA"):
            st.success("¡Datos capturados correctamente!")
            st.balloons()
            st.dataframe(df_editado)

except Exception as e:
    st.error(f"Error detectado: {e}")
