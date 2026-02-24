import streamlit as st
import pandas as pd

st.set_page_config(page_title="Control Orquesta", layout="wide")

st.title("🎻 Control de Asistencia y Evaluación")

st.info("Configurando conexión con Google Sheets...")

# Aquí es donde el profesor elegirá la orquesta
orquesta = st.selectbox("Selecciona la Orquesta", ["Cartón", "Alecrín", "Tulipán", "Margarida"])

st.write(f"Pasando lista para: **{orquesta}**")

# Tabla de ejemplo (la conectaremos a tu Excel en el siguiente paso)
datos_ejemplo = pd.DataFrame([
    {"Alumno": "Juan Pérez", "Instrumento": "Violín", "Asistencia": True, "Actitud": "Bien", "Concentración": 5},
    {"Alumno": "Ana López", "Instrumento": "Cello", "Asistencia": True, "Actitud": "Excelente", "Concentración": 4}
])

# Editor interactivo
st.data_editor(
    datos_ejemplo,
    column_config={
        "Asistencia": st.column_config.CheckboxColumn("¿Está?"),
        "Actitud": st.column_config.SelectboxColumn("Actitud", options=["Excelente", "Bien", "Regular", "Mal"]),
        "Concentración": st.column_config.NumberInputColumn("Concentración", min_value=1, max_value=5),
    },
    hide_index=True,
)

if st.button("Guardar datos"):
    st.success("¡Datos guardados! (Simulación)")
