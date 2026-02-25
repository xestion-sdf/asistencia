import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SDF - Asistencia Rápida", layout="wide")

# URLs estables
URL_LISTADO = "https://docs.google.com/spreadsheets/d/1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI/export?format=csv&gid=320023"
URL_DOCENTES = "https://docs.google.com/spreadsheets/d/1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI/export?format=csv&gid=1283708974"

@st.cache_data(ttl=300) # Guardamos los datos 5 min para que no cargue en cada clic
def cargar_datos(url):
    df = pd.read_csv(f"{url}&timestamp={datetime.now().day}")
    df.columns = df.columns.str.strip()
    return df

try:
    df_maestro = cargar_datos(URL_LISTADO)
    df_docentes = cargar_datos(URL_DOCENTES)
    
    st.sidebar.header("Configuración")
    docente_sel = st.sidebar.selectbox("Docente", ["Selecciona..."] + df_docentes.iloc[:,0].dropna().unique().tolist())
    orquesta_sel = st.sidebar.selectbox("Orquesta", df_maestro["Orquesta"].unique())
    
    # Filtrar y ordenar alfabéticamente para que NUNCA cambie el orden
    df_filtrado = df_maestro[
        (df_maestro["Orquesta"] == orquesta_sel) & 
        (df_maestro["Estado"].str.upper() == "ACTIVO")
    ].sort_values(by="NNA").copy()

    if docente_sel == "Selecciona...":
        st.info("👈 Selecciona docente")
    else:
        st.subheader(f"Lista {orquesta_sel}")
        
        # Diccionario para guardar lo que marques sin recargar la página
        asistencias = {}
        observaciones = {}

        # CREAMOS UNA FILA POR ALUMNO (Mucho más rápido)
        for i, row in df_filtrado.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 3])
                
                with col1:
                    st.write(f"**{row['NNA']}**")
                    st.caption(row['Instrumento'])
                
                with col2:
                    # Usamos un radio horizontal para que sea un solo clic
                    asistencias[row['NNA']] = st.radio(
                        f"Asistencia_{row['NNA']}",
                        options=["P", "FX", "FNX"],
                        horizontal=True,
                        label_visibility="collapsed",
                        key=f"asist_{row['NNA']}"
                    )
                
                with col3:
                    observaciones[row['NNA']] = st.text_input(
                        "Obs", 
                        placeholder="Nota u obs...", 
                        label_visibility="collapsed",
                        key=f"obs_{row['NNA']}"
                    )
                st.markdown("---")

        if st.button("🚀 GUARDAR TODO EL LISTADO"):
            # Aquí construimos el resultado final
            resumen = []
            for nombre in asistencias:
                resumen.append({
                    "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Alumno": nombre,
                    "Asistencia": asistencias[nombre],
                    "Observaciones": observaciones[nombre]
                })
            
            st.success("¡Datos listos para enviar!")
            st.table(pd.DataFrame(resumen))

except Exception as e:
    st.error(f"Error: {e}")
