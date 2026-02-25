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
