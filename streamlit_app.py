import streamlit as st
import pandas as pd
from datetime import datetime

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Control Orquesta SDF", layout="wide", page_icon="🎻")

st.title("🎻 Control de Asistencia y Evaluación")
st.markdown("---")

# 1. FUNCIÓN PARA CARGAR DATOS (Lectura directa para evitar Error 400)
# Usamos el ID de tu documento y el GID de cada pestaña
ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"

@st.cache_data(ttl=0) # ttl=0 para que siempre refresque los datos
def cargar_pestaña(gid):
    url = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={gid}"
    return pd.read_csv(url)

# Intentamos cargar las pestañas principales
try:
    # GID 320023 es LISTADO (según me dijiste antes)
    df_maestro = cargar_pestaña("320023") 
    
    # IMPORTANTE: Busca el GID de tu pestaña DOCENTES en la URL de tu navegador
    # Si no lo sabes, de momento usaremos un desplegable manual o intenta buscar el gid en la URL
    # Por ahora asumo el de LISTADO para que no de error, cambia el "0" por el GID de DOCENTES
    df_docentes = cargar_pestaña("1283708974") # Sustituye con el GID de la pestaña DOCENTES
except Exception as e:
    st.error(f"Error al conectar con las pestañas: {e}")
    st.info("Asegúrate de que el archivo esté compartido como 'Cualquier persona con el enlace puede EDITAR'")
    st.stop()

# 2. BARRA LATERAL (CONFIGURACIÓN)
st.sidebar.header("⚙️ Configuración de Sesión")

# Lista de docentes desde la pestaña DOCENTES
lista_docentes = df_docentes.iloc[:, 0].dropna().tolist() # Toma la primera columna
docente_sel = st.sidebar.selectbox("Docente responsable:", ["Selecciona..."] + lista_docentes)

# Lista de orquestas desde LISTADO
lista_orquestas = df_maestro["Orquesta"].unique()
orquesta_sel = st.sidebar.selectbox("Selecciona Orquesta:", lista_orquestas)

fecha_hoy = st.sidebar.date_input("Fecha de hoy:", datetime.now())

# 3. FILTRADO DE ALUMNOS
# Filtramos por orquesta y que estén ACTIVOS
df_filtrado = df_maestro[(df_maestro["Orquesta"] == orquesta_sel) & (df_maestro["Estado"] == "ACTIVO")].copy()

# 4. CUERPO DE LA APP
if docente_sel == "Selecciona...":
    st.info("👈 Por favor, selecciona tu nombre en la barra lateral para comenzar.")
else:
    st.subheader(f"📋 Lista: {orquesta_sel} | {len(df_filtrado)} alumnos")
    
    # Creamos la tabla editable
    # Columnas: NNA, Instrumento, V/F, Actitud, Nota, Observaciones
    df_editado = st.data_editor(
        df_filtrado[["NNA", "Instrumento", "V/F", "Actitud", "Nota", "Observaciones"]],
        column_config={
            "NNA": st.column_config.Column("Nombre del Alumno", disabled=True),
            "Instrumento": st.column_config.Column("Instrumento", disabled=True),
            "V/F": st.column_config.SelectboxColumn("Asistencia", options=["P", "FX", "FNX"], required=True),
            "Actitud": st.column_config.SelectboxColumn("Actitud", options=["🌟 Excelente", "✅ Bien", "⚠️ Regular", "❌ Mal"]),
            "Nota": st.column_config.NumberInputColumn("Conc. (1-5)", min_value=1, max_value=5, step=1),
            "Observaciones": st.column_config.TextColumn("Observaciones", width="large")
        },
        hide_index=True,
        use_container_width=True
    )

    # 5. BOTÓN DE GUARDADO
    if st.button("🚀 FINALIZAR Y GUARDAR EN HISTORIAL"):
        with st.spinner("Guardando datos..."):
            # Preparar los datos finales
            df_final = df_editado.copy()
            df_final["Fecha"] = fecha_hoy.strftime("%d/%m/%Y")
            df_final["Docente"] = docente_sel
            df_final["Orquesta"] = orquesta_sel
            
            # Reordenar columnas para que coincida con tu pestaña HISTORIAL
            columnas_historial = ["Fecha", "Orquesta", "Docente", "NNA", "Instrumento", "V/F", "Actitud", "Nota", "Observaciones"]
            df_final = df_final[columnas_historial]
            
            # MOSTRAR RESULTADO (Para probar antes de la escritura final)
            st.write("Datos procesados correctamente:")
            st.dataframe(df_final, hide_index=True)
            
            st.success("✅ ¡Asistencia procesada! (Para la escritura automática final necesitamos configurar el token de Google)")
            st.balloons()

# FOOTER
st.markdown("---")
st.caption("Sistema de Gestión de Orquestas - SDF 2026")
