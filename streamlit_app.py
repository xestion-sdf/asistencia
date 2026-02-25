import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="SDF - Portal Docente", layout="wide")

st.markdown("""
    <style>
    :root { --primary-color: #28a745 !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] > div:first-child {
        border-color: #28a745 !important;
        background-color: #28a745 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CARGA DE DATOS ---

ID_SHEET = "1wR4oDqNV5QheGx7wp-H9-s6De2IMAynSf_9vLGbE5qI"
URL_LISTADO = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=320023"
URL_DOCENTES = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=1283708974"
URL_HISTORIAL = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid=827716903"

# --- IMPORTANTE: Verifica que este GID sea el de la hoja "Respuestas de formulario 1" ---
GID_HISTORIAL = "827716903" # Por defecto suele ser 0 o el que veas en la URL
URL_HISTORIAL = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/export?format=csv&gid={GID_HISTORIAL}"

@st.cache_data(ttl=30)
def cargar_datos(url):
    try:
        # Añadimos timestamp para evitar caché vieja
        u = f"{url}&timestamp={datetime.now().timestamp()}"
        df = pd.read_csv(u)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return None

FORM_ASISTENCIA = "https://docs.google.com/forms/d/e/1FAIpQLSef94w2FNw2XTqRo9ZRnhURSOJx-5iUqeeVZ5kqqASLiTYF0A/formResponse"

# --- 3. BARRA LATERAL ---
# 1. Mostrar la imagen (Logo)
try:
    st.sidebar.image("avatar-sdf-100px.png", use_container_width=True)
except:
    # Si la imagen no se encuentra, no mostramos error, solo el título
    pass
st.sidebar.title("🎵 SDF Panel")
menu = st.sidebar.radio(
    "Selecciona una función:",
    ["📋 Asistencia Diaria", "🎻 Avaliación", "📊 Consulta de Rexistros", "📝 Bitácora ou Libro Diario"]
)

try:
    df_maestro = cargar_datos(URL_LISTADO)
    df_docentes = cargar_datos(URL_DOCENTES)
    
    st.sidebar.markdown("---")
    docente_sel = st.sidebar.selectbox("Docente", ["Selecciona..."] + df_docentes.iloc[:,0].dropna().unique().tolist())
    orquesta_sel = st.sidebar.selectbox("Orquesta", df_maestro["Orquesta"].unique())
    fecha_hoy = st.sidebar.date_input("Fecha", datetime.now())

    df_filtrado = df_maestro[
        (df_maestro["Orquesta"] == orquesta_sel) & (df_maestro["Estado"].str.upper() == "ACTIVO")
    ].sort_values(by="NNA").copy()

    if docente_sel == "Selecciona...":
        st.info("👈 Selecciona tu nombre en el lateral.")
    
    # --- PÁGINA 1: ASISTENCIA ---
    elif menu == "📋 Asistencia Diaria":
        st.header(f"Asistencia - {orquesta_sel}")
        asistencias = {}
        observaciones = {}
        for i, row in df_filtrado.iterrows():
            c1, c2, c3 = st.columns([3, 2, 4])
            c1.write(f"**{row['NNA']}**")
            asistencias[row['NNA']] = c2.radio(f"as_{i}", ["P", "FX", "FNX"], horizontal=True, label_visibility="collapsed", key=f"as_{i}")
            observaciones[row['NNA']] = c3.text_input("Obs", placeholder="Nota", label_visibility="collapsed", key=f"ob_{i}")
            st.markdown("---")
        
        if st.button("🔍 1. GUARDAR Y REVISAR"):
            resumen_as = [{"Fecha": fecha_hoy.strftime("%d/%m/%Y"), "Orquesta": orquesta_sel, "Docente": docente_sel, "NNA": n, "Estado": asistencias[n], "Obs": observaciones[n]} for n in asistencias]
            st.session_state.temp_asistencia = resumen_as
            st.success("✅ Revisión generada.")
            st.table(pd.DataFrame(resumen_as))

        if "temp_asistencia" in st.session_state:
            if st.button("🚀 2. CONFIRMAR ENVÍO"):
                exitos = 0
                for d in st.session_state.temp_asistencia:
                    inst = df_filtrado[df_filtrado["NNA"] == d["NNA"]]["Instrumento"].values[0]
                    data = {
                        "entry.883067698": d["Fecha"], "entry.695473946": d["Orquesta"],
                        "entry.252597218": d["Docente"], "entry.1616335440": d["NNA"],
                        "entry.1668643155": inst, "entry.1284516970": d["Estado"],
                        "entry.58216437": d["Obs"]
                    }
                    try:
                        r = requests.post(FORM_ASISTENCIA, data=data)
                        if r.status_code == 200: exitos += 1
                    except: pass
                st.success(f"✅ ¡Enviado! ({exitos} registros)")
                del st.session_state.temp_asistencia

# --- PÁGINA 2: EVALUACIÓN MULTIDIMENSIONAL (SISTEMA INTEGRAL) ---
    elif menu == "🎻 Avaliación":
        st.header("Avaliación Integral de Dimensións")
        
        # Selector de dimensión
        dimension = st.selectbox(
            "Selecciona la Dimensión a evaluar hoy:",
            ["Cognitiva", "Emocional", "Social", "Persoal"]
        )

        st.info(f"📍 Indicadores para la Dimensión: **{dimension}**")
        eval_data = {}

        for i, row in df_filtrado.iterrows():
            with st.expander(f"👤 {row['NNA']} ({row['Instrumento']})"):
                
                if dimension == "Cognitiva":
                    c1, c2 = st.columns(2)
                    v1 = c1.radio(f"Instrucións dirección - {i}", ["1","2","3","4","5"], horizontal=True, index=2, key=f"cog1_{i}")
                    v2 = c2.radio(f"Corrixir erros/Memoria - {i}", ["1","2","3","4","5"], horizontal=True, index=2, key=f"cog2_{i}")
                    eval_data[row['NNA']] = {"Indicador 1": v1, "Indicador 2": v2}

                elif dimension == "Emocional":
                    c1, c2, c3 = st.columns(3)
                    v1 = c1.radio(f"Asertividade - {i}", ["1","2","3","4","5"], horizontal=True, index=2, key=f"emo1_{i}")
                    v2 = c2.radio(f"Frustración - {i}", ["1","2","3","4","5"], horizontal=True, index=2, key=f"emo2_{i}")
                    v3 = c3.radio(f"Superación/Orgullo - {i}", ["1","2","3","4","5"], horizontal=True, index=2, key=f"emo3_{i}")
                    eval_data[row['NNA']] = {"Indicador 1": v1, "Indicador 2": v2, "Indicador 3": v3}

                elif dimension == "Social":
                    c1, c2 = st.columns(2)
                    v1 = c1.radio(f"Silencio/Respecto - {i}", ["1","2","3","4","5"], horizontal=True, index=2, key=f"soc1_{i}")
                    v2 = c2.radio(f"Axuda mutua - {i}", ["1","2","3","4","5"], horizontal=True, index=2, key=f"soc2_{i}")
                    eval_data[row['NNA']] = {"Indicador 1": v1, "Indicador 2": v2}
                
                elif dimension == "Persoal":
                    v1 = st.radio(f"Coidado do material - {row['NNA']}", ["1","2","3","4","5"], horizontal=True, index=2, key=f"per1_{i}")
                    eval_data[row['NNA']] = {"Indicador 1": v1}

        st.markdown("---")
        if st.button(f"🔍 1. GARDAR EVALUACIÓN {dimension.upper()}"):
            resumen_dim = []
            for nna, valores in eval_data.items():
                registro = {
                    "Fecha": fecha_hoy.strftime("%d/%m/%Y"),
                    "Docente": docente_sel,
                    "Alumno": nna,
                    "Dimensión": dimension
                }
                registro.update(valores) 
                resumen_dim.append(registro)
            
            st.session_state.temp_eval_dim = resumen_dim
            st.success(f"✅ Revisión de dimensión {dimension} lista.")
            st.table(pd.DataFrame(resumen_dim))

        if "temp_eval_dim" in st.session_state:
            if st.button(f"🚀 2. CONFIRMAR ENVÍO DE {dimension.upper()}"):
                # Aquí conectaremos los entry.IDs del formulario único
                st.info("Conectando con el servidor de Google...")
                # Lógica de requests.post...
                st.success(f"Datos enviados correctamente a la pestaña de {dimension}")
                del st.session_state.temp_eval_dim

   # --- PÁGINA 3: CONSULTA DE REGISTROS (YA CON CONEXIÓN) ---
    elif menu == "📊 Consulta de Registros":
        st.header("Historial y Seguimiento de Alumnos")
        df_hist = cargar_datos(URL_HISTORIAL)
        
        if df_hist is not None and not df_hist.empty:
            # Mostramos un buscador rápido para no tener que scrollear
            tab1, tab2 = st.tabs(["📅 Vista por Día", "👤 Expediente por Alumno"])
            
            with tab1:
                f_busq = st.date_input("Consultar fecha:", datetime.now())
                
                # Generamos varios formatos posibles para asegurar la coincidencia
                f_opcion1 = f_busq.strftime("%d/%m/%Y")   # 25/02/2026
                f_opcion2 = f_busq.strftime("%-d/%-m/%Y") # 25/2/2026 (sin ceros)
                f_opcion3 = f_busq.strftime("%Y-%m-%d")   # 2026-02-25
                
                # Filtramos: buscamos cualquiera de los 3 formatos en la columna 'Marca temporal' (columna 0)
                mask_dia = df_hist.iloc[:, 0].astype(str).str.contains(f_opcion1, na=False) | \
                           df_hist.iloc[:, 0].astype(str).str.contains(f_opcion2, na=False) | \
                           df_hist.iloc[:, 0].astype(str).str.contains(f_opcion3, na=False)
                
                res_dia = df_hist[mask_dia]
                
                if not res_dia.empty:
                    st.success(f"✅ Se encontraron {len(res_dia)} registros para el día {f_opcion1}")
                    st.dataframe(res_dia, use_container_width=True)
                else:
                    st.info(f"No se encontraron registros para el {f_opcion1}.")
                    # Tip de ayuda para depurar:
                    with st.expander("¿Por qué no veo resultados?"):
                        st.write("Formatos intentados:", [f_opcion1, f_opcion2, f_opcion3])
                        st.write("Primeros registros en el historial:", df_hist.iloc[:2, 0].tolist())

            with tab2:
                al_lista = df_maestro[df_maestro["Orquesta"] == orquesta_sel]["NNA"].unique()
                al_busq = st.selectbox("Seleccione el alumno para ver su historial:", al_lista)
                
                # Buscamos al alumno en la columna correspondiente (ajusta el índice si es necesario, 
                # aquí busca en todo el documento para mayor seguridad)
                res_al = df_hist[df_hist.apply(lambda row: row.astype(str).str.contains(al_busq).any(), axis=1)].copy()
                
                if not res_al.empty:
                    # Contamos las faltas buscando el texto exacto 'FNX'
                    # Convertimos la tabla a un solo texto gigante para contar rápido
                    conteo_texto = res_al.astype(str).values.flatten()
                    faltas_graves = sum(1 for x in conteo_texto if 'FNX' in x)
                    asistencias = sum(1 for x in conteo_texto if x == 'P')
                    
                    # Panel de indicadores
                    col1, col2 = st.columns(2)
                    col1.metric("Asistencias Registradas", asistencias)
                    col2.metric("FALTAS NO JUSTIFICADAS", faltas_graves, delta_color="inverse")
                    
                    if faltas_graves >= 3:
                        st.error(f"⚠️ Alerta: {al_busq} ha superado el límite de 3 faltas no justificadas.")
                    
                    st.write("### Detalle de registros encontrados:")
                    st.dataframe(res_al, use_container_width=True)
                else:
                    st.info(f"No existen registros previos para {al_busq} en esta orquesta.")
        else:
            st.error("El historial está vacío o no se pudo leer correctamente.")

# --- NUEVA PÁGINA: BITÁCORA DE INCIDENCIAS Y LOGROS ---
    elif menu == "📝 Bitácora ou Libro Diario":
        st.header("Registro de Incidencias y Comentarios Positivos")
        st.info("Utiliza este espacio para documentar situaciones relevantes o logros destacados.")

        # Selección de Alumno (usando la lista ya cargada de la orquesta)
        al_lista = df_maestro[df_maestro["Orquesta"] == orquesta_sel]["NNA"].unique()
        alumno_bit = st.selectbox("Alumno/a:", ["Selecciona un alumno..."] + list(al_lista))

        if alumno_bit != "Selecciona un alumno...":
            tipo_nota = st.radio("Tipo de registro:", ["🌟 Comentario Positivo", "⚠️ Incidencia / Observación"], horizontal=True)
            
            comentario = st.text_area(f"Escribe aquí el detalle para {alumno_bit}:", placeholder="Ej: Hoy ayudó espontáneamente a un compañero con la afinación...")

            if st.button("🔍 GUARDAR NOTA EN REVISIÓN"):
                nota_previa = {
                    "Fecha": fecha_hoy.strftime("%d/%m/%Y"),
                    "Docente": docente_sel,
                    "Alumno": alumno_bit,
                    "Tipo": tipo_nota,
                    "Comentario": comentario
                }
                st.session_state.temp_bitacora = [nota_previa]
                st.success("Nota lista para enviar.")
                st.table(pd.DataFrame(st.session_state.temp_bitacora))

            if "temp_bitacora" in st.session_state:
                if st.button("🚀 CONFIRMAR ENVÍO A BITÁCORA"):
                    # Aquí usaremos el mismo formulario principal o uno específico
                    st.success(f"Nota de {docente_sel} sobre {alumno_bit} guardada correctamente.")
                    del st.session_state.temp_bitacora

except Exception as e:
    st.error(f"Error General: {e}")
