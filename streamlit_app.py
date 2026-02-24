import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Control Orquesta", layout="wide")

st.title("🎻 Pase de Lista y Valoración")

# 1. Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Leer los datos (Carga la pestaña LISTADO_MAESTRO)
# Nota: Asegúrate de que el nombre de la hoja coincide exactamente
df = conn.read(worksheet="LISTADO_MAESTRO", ttl="5m")

# 3. Interfaz de Filtros
st.sidebar.header("Configuración")
orquesta_sel = st.sidebar.selectbox("Selecciona Orquesta", df["Orquesta"].unique())

# Filtrar alumnos activos de esa orquesta
df_filtrado = df[(df["Orquesta"] == orquesta_sel) & (df["Estado"] == "ACTIVO")].copy()

st.subheader(f"Lista de {orquesta_sel}")
st.write("Marca la asistencia y evalúa a cada alumno:")

# 4. Tabla Interactiva (Editor)
# Aquí puedes cambiar la actitud y concentración directamente
df_editado = st.data_editor(
    df_filtrado[["Alumno", "Instrumento", "Actitud", "Concentracion"]],
    column_config={
        "Alumno": st.column_config.Column(disabled=True),
        "Instrumento": st.column_config.Column(disabled=True),
        "Actitud": st.column_config.SelectboxColumn(
            "Actitud", 
            options=["🌟 Excelente", "✅ Bien", "⚠️ Regular", "❌ Mal"],
            required=True
        ),
        "Concentracion": st.column_config.NumberInputColumn(
            "Concentración (1-5)",
            min_value=1,
            max_value=5,
            step=1,
            format="%d"
        )
    },
    hide_index=True,
    use_container_width=True
)

# 5. Botón de Guardar
if st.button("Guardar Asistencia de Hoy"):
    # Aquí podrías añadir lógica para guardar en una pestaña de HISTORIAL
    st.success(f"¡Asistencia de {orquesta_sel} procesada!")
    st.balloons()
