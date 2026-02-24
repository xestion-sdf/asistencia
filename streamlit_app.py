import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Control Orquesta", layout="wide")

st.title("🎻 Control de Asistencia y Evaluación")

# 1. Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Carga de datos
df = conn.read(worksheet="LISTADO_MAESTRO", ttl="0")
df_docentes = conn.read(worksheet="DOCENTES", ttl="10m")

# 3. BARRA LATERAL (Filtros maestros)
st.sidebar.header("Datos de la Sesión")
lista_docentes = df_docentes["Nombre"].tolist()
docente_sel = st.sidebar.selectbox("Docente", options=["Selecciona..."] + lista_docentes)
fecha_hoy = st.sidebar.date_input("Fecha", datetime.now())
orquesta_sel = st.sidebar.selectbox("Selecciona Orquesta", df["Orquesta"].unique())

# 4. FILTROS DE BÚSQUEDA RÁPIDA (Encima de la tabla)
col1, col2 = st.columns(2)
with col1:
    busqueda = st.text_input("🔍 Buscar por nombre de alumno...")
with col2:
    instrumento_sel = st.multiselect("Filtrar por Instrumento", options=sorted(df["Instrumento"].unique()))

# 5. LÓGICA DE FILTRADO
# Filtramos por Orquesta y Estado Activo
mask = (df["Orquesta"] == orquesta_sel) & (df["Estado"] == "ACTIVO")

# Si hay búsqueda por texto
if busqueda:
    mask = mask & (df["NNA"].str.contains(busqueda, case=False, na=False))

# Si hay filtro de instrumento
if instrumento_sel:
    mask = mask & (df["Instrumento"].isin(instrumento_sel))

df_final = df[mask].copy()

# 6. TABLA INTERACTIVA
st.subheader(f"Listado: {orquesta_sel} ({len(df_final)} alumnos)")

df_editado = st.data_editor(
    df_final[["NNA", "Instrumento", "V/F", "Actitud", "Nota", "Observaciones"]],
    column_config={
        "NNA": st.column_config.Column("Alumno", disabled=True, width="medium"),
        "Instrumento": st.column_config.Column(disabled=True, width="small"),
        "V/F": st.column_config.SelectboxColumn("Asistencia", options=["P", "FX", "FNX"], required=True),
        "Actitud": st.column_config.SelectboxColumn("Actitud", options=["🌟 Excelente", "✅ Bien", "⚠️ Regular", "❌ Mal"]),
        "Nota": st.column_config.NumberInputColumn("Conc.", min_value=1, max_value=5, step=1),
        "Observaciones": st.column_config.TextColumn("Observaciones", width="large")
    },
    hide_index=True,
    use_container_width=True
)

# 7. GUARDADO
if st.button("🚀 Finalizar y Guardar en Historial"):
    if docente_sel == "Selecciona...":
        st.error("⚠️ Elige un docente en el menú lateral.")
    else:
        # Preparamos los datos
        df_historial = df_editado.copy()
        df_historial["Fecha"] = fecha_hoy.strftime("%d/%m/%Y")
        df_historial["Orquesta"] = orquesta_sel
        df_historial["Docente"] = docente_sel
        
        columnas = ["Fecha", "Orquesta", "Docente", "NNA", "Instrumento", "V/F", "Actitud", "Nota", "Observaciones"]
        df_historial = df_historial[columnas]
        
        try:
            # Opción segura para añadir datos sin borrar lo anterior
            existing_data = conn.read(worksheet="HISTORIAL")
            updated_data = pd.concat([existing_data, df_historial], ignore_index=True)
            conn.update(worksheet="HISTORIAL", data=updated_data)
            
            st.success(f"¡Se han registrado {len(df_historial)} registros en el Historial!")
            st.balloons()
        except Exception as e:
            st.error(f"Error: Asegúrate de que la pestaña 'HISTORIAL' tenga los encabezados correctos. {e}")
