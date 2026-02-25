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

# --- IMPORTANTE: Verifica que este GID sea el de la hoja "Respuestas de formulario 1" ---
GID_HISTORIAL = "0" # Por defecto suele ser 0 o el que veas en la URL
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
st.sidebar.title("🎵 SDF Panel")
menu = st.sidebar.radio(
    "Selecciona una función:",
    ["📋 Asistencia Diaria", "🎻 Evaluación Técnica", "📊 Consulta de Registros"]
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

    # --- PÁGINA 2: EVALUACIÓN ---
    elif menu == "🎻 Evaluación Técnica":
        st.header("Evaluación Integral")
        # Aquí iría el código de los expansores (igual que antes)
        st.write("Configura el formulario de evaluación para activar.")

   # --- PÁGINA 3: CONSULTA DE REGISTROS CON CONTADOR DE FALTAS ---
    elif menu == "📊 Consulta de Registros":
        st.header("Historial y Seguimiento")
        df_hist = cargar_datos(URL_HISTORIAL)
        
        if df_hist is not None and not df_hist.empty:
            tab1, tab2 = st.tabs(["📅 Registros por Día", "📈 Resumen por Alumno"])
            
            with tab1:
                f_busq = st.date_input("Selecciona el día", datetime.now())
                f_str_1 = f_busq.strftime("%Y-%m-%d")
                f_str_2 = f_busq.strftime("%d/%m/%Y")
                
                # Filtro por fecha en Marca Temporal
                res_dia = df_hist[df_hist.iloc[:, 0].astype(str).str.contains(f_str_1, na=False) | 
                                 df_hist.iloc[:, 0].astype(str).str.contains(f_str_2, na=False)]
                
                if not res_dia.empty:
                    st.write(f"### Registros del {f_str_2}")
                    st.dataframe(res_dia, use_container_width=True)
                else:
                    st.info("No hay registros para esta fecha.")

            with tab2:
                al_lista = df_maestro[df_maestro["Orquesta"] == orquesta_sel]["NNA"].unique()
                al_busq = st.selectbox("Selecciona un alumno", al_lista)
                
                # Filtramos registros del alumno
                res_al = df_hist[df_hist.apply(lambda row: row.astype(str).str.contains(al_busq).any(), axis=1)].copy()
                
                if not res_al.empty:
                    # --- CÁLCULO DE FALTAS ---
                    # Buscamos en todas las columnas el texto 'FNX'
                    total_fnx = res_al.apply(lambda row: row.astype(str).str.contains('FNX').any(), axis=1).sum()
                    total_fx = res_al.apply(lambda row: row.astype(str).str.contains('FX').any(), axis=1).sum()
                    total_p = res_al.apply(lambda row: row.astype(str).str.contains('P', case=False).any(), axis=1).sum()

                    # Mostrar alertas visuales
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Asistencias (P)", total_p)
                    c2.metric("Faltas Justificadas (FX)", total_fx)
                    # La métrica de faltas no justificadas resalta en rojo si es mayor a 0
                    c3.metric("FALTAS NO JUSTIFICADAS (FNX)", total_fnx, delta_color="inverse")

                    if total_fnx >= 3:
                        st.error(f"⚠️ ATENCIÓN: {al_busq} tiene {total_fnx} faltas no justificadas. Se recomienda contactar al apoderado.")
                    elif total_fnx > 0:
                        st.warning(f"Nota: El alumno registra {total_fnx} faltas no justificadas.")

                    st.write("### Detalle Histórico")
                    st.dataframe(res_al, use_container_width=True)
                else:
                    st.info(f"No hay registros previos para {al_busq}.")
        else:
            st.error("No se pudo cargar el historial. Revisa el GID de la pestaña de respuestas.")

except Exception as e:
    st.error(f"Error general: {e}")
