# --- PÁGINA 3: CONSULTA DE REGISTROS CON SEMÁFORO DE FALTAS ---
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
                mask_dia = df_hist.iloc[:, 0].astype(str).str.contains(f_str_1, na=False) | \
                           df_hist.iloc[:, 0].astype(str).str.contains(f_str_2, na=False)
                res_dia = df_hist[mask_dia]
                
                if not res_dia.empty:
                    st.write(f"### Registros del {f_busq.strftime('%d/%m/%Y')}")
                    st.dataframe(res_dia, use_container_width=True)
                else:
                    st.info("No hay registros para esta fecha.")

            with tab2:
                al_lista = df_maestro[df_maestro["Orquesta"] == orquesta_sel]["NNA"].unique()
                al_busq = st.selectbox("Selecciona un alumno", al_lista)
                
                # Filtramos registros del alumno buscando su nombre en cualquier columna
                res_al = df_hist[df_hist.apply(lambda row: row.astype(str).str.contains(al_busq).any(), axis=1)].copy()
                
                if not res_al.empty:
                    # --- CONTEO DE ASISTENCIAS ---
                    # Convertimos todo a texto para buscar los estados
                    texto_total = res_al.astype(str).values.flatten()
                    
                    total_p = sum("P" == x for x in texto_total)
                    total_fx = sum("FX" == x for x in texto_total)
                    total_fnx = sum("FNX" == x for x in texto_total)

                    # Mostrar métricas visuales
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Presentes (P)", total_p)
                    m2.metric("Justificadas (FX)", total_fx)
                    m3.metric("FALTAS SIN JUSTIFICAR (FNX)", total_fnx, delta_color="inverse")

                    # ALERTAS CRÍTICAS
                    if total_fnx >= 3:
                        st.error(f"🚨 ALERTA CRÍTICA: {al_busq} tiene {total_fnx} faltas no justificadas.")
                        st.button("📧 Notificar a Coordinación")
                    elif total_fnx > 0:
                        st.warning(f"⚠️ El alumno registra {total_fnx} inasistencias sin justificación.")

                    st.write("### Detalle Cronológico")
                    st.dataframe(res_al, use_container_width=True)
                else:
                    st.info(f"No hay registros previos para {al_busq}.")
        else:
            st.error("No se pudo cargar el historial. Revisa que el GID sea el de la pestaña de respuestas.")

# Este except debe estar al final del todo, alineado con el try inicial
except Exception as e:
    st.error(f"Error general en la aplicación: {e}")
