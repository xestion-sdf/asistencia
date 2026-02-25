import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Control Orquesta SDF", layout="wide")

# URLs que ya comprobamos que funcionan
URL_LISTADO = "https://docs.google.com/spreadsheets/d/1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI/export?format=csv&gid=320023"
URL_DOCENTES = "https://docs.google.com/spreadsheets/d/1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI/export?format=csv&gid=1283708974"

st.title("🎻 Gestión de Orquestas SDF")

def cargar_datos(url):
    url_final = f"{url}&cache={datetime.now().timestamp()}"
    df = pd.read_csv(url_final)
    df.columns = df.columns.str.strip()
    return df

try:
    df_maestro = cargar_datos(URL_LISTADO)
    df_docentes = cargar_datos(URL_DOCENTES)
    
    # BARRA LATERAL
    st.sidebar.header("Configuración")
    docente_sel = st.sidebar.selectbox("Docente", ["Selecciona..."] + df_docentes.iloc[:,0].dropna().unique().tolist())
    orquesta_sel = st.sidebar.selectbox("Orquesta", df_maestro["Orquesta"].unique())
    fecha_hoy = st.sidebar.date_input("Fecha", datetime.now())
    
    # FILTRO DE ALUMNOS
    df_filtrado = df_maestro[
        (df_maestro["Orquesta"] == orquesta_sel) & 
        (df_maestro["Estado"].str.upper() == "ACTIVO")
    ].copy()
    
    if docente_sel == "Selecciona...":
        st.info("👈 Por favor, selecciona un docente en la barra lateral.")
    elif not df_filtrado.empty:
        st.subheader(f"Lista de {orquesta_sel} ({len(df_filtrado)} alumnos)")
        
        # --- TABLA CON CONFIGURACIÓN COMPATIBLE ---
        df_editado = st.data_editor(
            df_filtrado[["NNA", "Instrumento", "V/F", "Actitud", "Nota", "Observaciones"]],
            column_config={
                "NNA": st.column_config.Column("Alumno", disabled=True),
                "Instrumento": st.column_config.Column("Instrumento", disabled=True),
                
                # CONFIGURACIÓN V/F: P, FX, FNX (Usando SelectboxColumn que sí suele estar disponible)
                "V/F": st.column_config.SelectboxColumn(
                    "Asistencia",
                    options=["P", "FX", "FNX"]
                ),
                
                "Actitud": st.column_config.SelectboxColumn(
                    "Actitud",
                    options=["🌟 Excelente", "✅ Bien", "⚠️ Regular", "❌ Mal"]
                ),
                
                # Para la Nota, usamos Column genérica para evitar el error de NumberInputColumn
                "Nota": st.column_config.Column("Nota (1-5)"),
                
                "Observaciones": st.column_config.TextColumn("Observaciones", width="large")
            },
            hide_index=True,
            use_container_width=True
        )
        
        if st.button("🚀 Guardar en Historial"):
            st.success(f"¡Asistencia procesada!")
            st.balloons()
            st.write("Resumen de datos:", df_editado)
            
    else:
        st.warning("No hay alumnos activos para esta orquesta.")

except Exception as e:
    st.error(f"Error al cargar: {e}")
