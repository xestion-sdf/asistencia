import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Control Orquesta SDF", layout="wide")

URL_LISTADO = "https://docs.google.com/spreadsheets/d/1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI/export?format=csv&gid=320023"
URL_DOCENTES = "https://docs.google.com/spreadsheets/d/1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI/export?format=csv&gid=1283708974"

st.title("🎻 Gestión de Orquestas SDF")

def cargar_datos(url):
    url_final = f"{url}&cache={datetime.now().timestamp()}"
    df = pd.read_csv(url_final)
    df.columns = df.columns.str.strip()
    
    # --- SOLUCIÓN AL ERROR DE TIPO DE DATOS ---
    # Forzamos a que estas columnas sean SIEMPRE texto, incluso si están vacías
    columnas_texto = ["V/F", "Actitud", "Observaciones", "Nota"]
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).replace("nan", "")
            
    return df

try:
    df_maestro = cargar_datos(URL_LISTADO)
    df_docentes = cargar_datos(URL_DOCENTES)
    
    st.sidebar.header("Configuración")
    docente_sel = st.sidebar.selectbox("Docente", ["Selecciona..."] + df_docentes.iloc[:,0].dropna().unique().tolist())
    orquesta_sel = st.sidebar.selectbox("Orquesta", df_maestro["Orquesta"].unique())
    fecha_hoy = st.sidebar.date_input("Fecha", datetime.now())
    
    df_filtrado = df_maestro[
        (df_maestro["Orquesta"] == orquesta_sel) & 
        (df_maestro["Estado"].str.upper() == "ACTIVO")
    ].copy()
    
    if docente_sel == "Selecciona...":
        st.info("👈 Selecciona un docente en la barra lateral.")
    elif not df_filtrado.empty:
        st.subheader(f"Lista de {orquesta_sel}")
        
        # TABLA DEFINITIVA
        df_editado = st.data_editor(
            df_filtrado[["NNA", "Instrumento", "V/F", "Actitud", "Nota", "Observaciones"]],
            column_config={
                "NNA": st.column_config.Column("Alumno", disabled=True),
                "Instrumento": st.column_config.Column("Instrumento", disabled=True),
                "V/F": st.column_config.SelectboxColumn(
                    "Asistencia",
                    options=["P", "FX", "FNX"]
                ),
                "Actitud": st.column_config.SelectboxColumn(
                    "Actitud",
                    options=["🌟 Excelente", "✅ Bien", "⚠️ Regular", "❌ Mal"]
                ),
                "Nota": st.column_config.Column("Nota (1-5)"),
                "Observaciones": st.column_config.TextColumn("Observaciones", width="large")
            },
            hide_index=True,
            use_container_width=True
        )
        
        if st.button("🚀 Procesar Asistencia"):
            st.success("¡Datos capturados correctamente!")
            st.balloons()
            st.dataframe(df_editado)
            
    else:
        st.warning("No hay alumnos activos para esta orquesta.")

except Exception as e:
    st.error(f"Error al cargar: {e}")
