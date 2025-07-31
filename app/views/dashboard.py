import streamlit as st
import pandas as pd
from views.cargar import CargarArchivosView
from controllers.auth import Auth
from controllers.dashboard import DashBoard
import plotly.express as px

cargarAchivos = CargarArchivosView()
dashboard = DashBoard()

@st.cache_data
def cargar_datos(periodo, periodoPrevio, ciclo, ruta):
    return {
        "actual": dashboard.getResultados(periodo, ciclo, ruta),
        "previo": dashboard.getResultados(periodoPrevio, ciclo, ruta),
        "foto_actual": dashboard.getFrecuenciaFotoLectura(periodo, ciclo, ruta),
        "foto_previo": dashboard.getFrecuenciaFotoLectura(periodoPrevio, ciclo, ruta),
        "carga_actual": dashboard.getCargaLaboral(periodo),
        "carga_previo": dashboard.getCargaLaboral(periodoPrevio),
        "escala_actual": dashboard.getEscaladoRuta(periodo, ciclo, ruta),
        "escala_previo": dashboard.getEscaladoRuta(periodoPrevio, ciclo, ruta)
    }

def convertir_horas_minutos(minutos):
    horas = int(minutos // 60)
    mins = int(minutos % 60)
    return f"{horas}h {mins}m"

def convertir_segundos_a_horas_minutos(segundos):
    minutos_redondeados = round(segundos / 60)
    horas = minutos_redondeados // 60
    minutos = minutos_redondeados % 60
    return f"{horas}h {minutos}m"


def asignar_nivel(valor):
    if valor > 3:
        return '🔶 Advertencia'
    elif valor == 3:
        return '⚠️ Inusual'
    else:
        return '✅ Verificar'

class DashboardView:
    def __init__(self):
        self.authController = Auth()
        self.dashboard = DashBoard() 
    
    def mostrar_metrica(self, label, valor_actual, valor_anterior, delta_color=None, detalles=None, dfCompleto=None):
        delta = round(valor_actual - valor_anterior, 2)
        col1, col2 = st.columns([4, 1])
        col1.metric(label=label, value=f"{valor_actual}%", delta=f"{delta}%", delta_color=delta_color)
        if col2.button('👁', key=f'btn_{label}'):
            if label == '% Carga Laboral 📦':
                st.session_state.filtros_habilitados = False
            st.session_state.vista_actual = label
            st.session_state.df_detalles = detalles
            st.session_state.df_actual = dfCompleto
            st.rerun()

    def volver_al_tablero(self):
        st.session_state.pop('vista_actual', None)
        st.session_state.pop('df_detalles', None)
        st.session_state.filtros_habilitados = True

    def vista_detalles(self, df, label="Detalles", df_actual=None, periodo=None, ciclo=None, ruta=None):
        st.button('🔙 Volver al tablero', on_click=self.volver_al_tablero)
        st.subheader(label)
        if label == '% Carga Laboral 📦':
            lecturistas = df["lecturista"].unique()
            lecturistas_totales = df_actual["lecturista"].unique()
            porcentaje_lecturistas = len(lecturistas) * 100  / len(lecturistas_totales)

            df['Tiempo Total'] = df["tiempo_trabajado"].apply(convertir_horas_minutos)
            df['Tiempo Final'] = df["tiempo_neto"].apply(convertir_horas_minutos)
            df_actual['Tiempo Ejecucion Ruta'] = df_actual["tiempoEjecucionRuta"].apply(convertir_segundos_a_horas_minutos)
            df.rename(columns={'tiempo_de_reduccion': 'Tiempo Comida'}, inplace=True)
            df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
            
            col1, col2 = st.columns([1,3])
            with col1:
                st.progress(100, text=f'Total de lecturadores: {len(lecturistas_totales)}')
                st.progress(round(porcentaje_lecturistas), text=f'Lecturadores con carga laboral: {len(lecturistas)}')

                conteo_fechas = df["fecha"].value_counts().sort_index(ascending=True)
                conteo_df = conteo_fechas.reset_index()
                conteo_df.columns = ["Fechas Lectura", "# Lecturadores con carga"]
                conteo_df["Fechas Lectura"] = conteo_df["Fechas Lectura"].astype(str)

                st.line_chart(data=conteo_df.set_index("Fechas Lectura"), x_label='# Lecturadores con carga', y_label='Fechas Lectura', use_container_width=True)

            with col2:
                with st.expander('📊 Análisis por lecturador', expanded=False):
                    df_actual["fechaEjecucion"] = pd.to_datetime(df_actual["fechaEjecucion"]).dt.date

                    lecturistaSeleccionado = st.selectbox('Datos de lectura de: ', lecturistas, key='selectLecturista_carga')

                    df_lecturista = df[df['lecturista'] == lecturistaSeleccionado]
                    st.dataframe(df_lecturista[['fecha','suministro','Tiempo Total','Tiempo Comida','Tiempo Final', 'inicio','fin']], hide_index=True)


                    fechas = df_lecturista["fecha"].unique()
                    fechaSeleccionado = st.selectbox('Rutas leturadas en la fecha: ', fechas, key='selectFecha')

                    resultado = df_actual[
                        (df_actual['fechaEjecucion'] == fechaSeleccionado) &
                        (df_actual['lecturista'] == lecturistaSeleccionado)
                    ][['ciclo', 'ruta', 'tiempoTrabajado']].groupby(['ciclo', 'ruta']).agg(
                        Minutos=('tiempoTrabajado', lambda x: round(x.sum())),
                        Total=('ruta', 'size')
                    ).reset_index()

                    resultado["Tiempo Trabajado"] = resultado["Minutos"].apply(convertir_horas_minutos)

                    st.dataframe(resultado[['ciclo','ruta','Tiempo Trabajado','Total']], hide_index=True)

            with st.expander('📊 Análisis de todos los lecturadores con carga'):
                st.dataframe(df[['lecturista','fecha' ,'Tiempo Total', 'Tiempo Comida','Tiempo Final','suministro','inicio','fin']], hide_index=True)

                fechas_unicas = sorted(df["fecha"].unique())
                tabs = st.tabs([str(fecha) for fecha in fechas_unicas])

                for i, fecha in enumerate(fechas_unicas):
                    with tabs[i]:
                        st.subheader(f"Tiempo trabajado por lecturadores - {fecha} (en minutos)")
                        df_fecha = df[df["fecha"] == fecha]
                        st.bar_chart(df_fecha.set_index("lecturista")["tiempo_trabajado"])

        if label == '% Rutas con varios lecturadores 👥':
            col1, col2 = st.columns(2)

            with col1:
                tabla_rutas = df.groupby('ruta')['lecturista'].nunique().reset_index(name='# Lecturadores')
                tabla_rutas = tabla_rutas.sort_values(by='# Lecturadores', ascending=False)
                tabla_rutas['Indicador'] = tabla_rutas['# Lecturadores'].apply(asignar_nivel)
                tabla_agrupada = tabla_rutas.groupby('Indicador').size().reset_index(name='Cantidad')
                colores_fijos = {
                    '✅ Verificar': "#94F3BB",   # verde
                    '⚠️ Inusual': "#F4E4A6",     # amarillo
                    '🔶 Advertencia': "#FFA9A0"  # rojo
                }
                fig = px.pie(
                    tabla_agrupada,
                    values='Cantidad',
                    names='Indicador',
                    title='Distribución de Rutas según Indicador de Lecturadores',
                    hole=0.4,
                    color='Indicador',
                    color_discrete_map=colores_fijos
                )

                fig.update_traces(
                    textinfo='label+percent',
                    hovertemplate='%{label}<br>%{value} rutas'
                )

                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.dataframe(tabla_rutas.set_index('# Lecturadores'))

            col1, col2 = st.columns([2,1])
            with col1:
                selectRuta = st.selectbox('Lecturadores por ruta', tabla_rutas['ruta'])
                dfRuta = df[df['ruta'] == selectRuta]

                tiempo_total_por_lecturista = dfRuta.groupby('lecturista')['tiempo_lectura'].sum().reset_index()
                df_actual = df_actual[df_actual['ruta'] == selectRuta]
                df_cantidad = df_actual.groupby('lecturista').size().reset_index(name='# Suministros')

                tiempo_total_por_lecturista = tiempo_total_por_lecturista.sort_values(by='tiempo_lectura', ascending=False)
                tiempo_total_por_lecturista['Tiempo Lectura'] = tiempo_total_por_lecturista["tiempo_lectura"].apply(convertir_horas_minutos)
                df_final = pd.merge(tiempo_total_por_lecturista, df_cantidad, on='lecturista', how='left').fillna(0)
                st.dataframe(df_final[['lecturista','Tiempo Lectura', '# Suministros']].set_index('Tiempo Lectura'))
            
            with col2:
                selectLecturador = st.selectbox('Suministros por lecturador', df_final['lecturista'])
                df_actual = df_actual[(df_actual['ruta'] == selectRuta) & (df_actual['lecturista'] == selectLecturador)]
                st.dataframe(df_actual[['suministro']], hide_index=True)

        if label == '% Ejecucion de ruta anómala 😵‍💫':

            col1, col2 = st.columns([1,2])
            df['fecha'] = pd.to_datetime(df["inicio"]).dt.date
            lecturistas = df["lecturista"].unique()
            with col1:
                selectLecturador = st.selectbox('Lecturador:', lecturistas)

            df_lect = df[df["lecturista"] == selectLecturador].copy()
            df_lect["inicio"] = pd.to_datetime(df_lect["inicio"])
            df_lect["fin"] = pd.to_datetime(df_lect["fin"])
            df_lect.sort_values("inicio", inplace=True)

            fechas = df_lect["fecha"].unique()
            with col1:
                fecha_seleccionado = st.selectbox('Rutas leturadas en la fecha: ', fechas, key='selectFecha_anomalos')
    
            df_lect["Grupo"] = range(1, len(df_lect)+1)
            df_grafico = df_lect[df_lect['fecha'] == fecha_seleccionado] 
            fig = px.scatter(
                df_grafico,
                x="inicio",
                y="ruta",
                color="ruta",
                text="Grupo",
                hover_data=["inicio", "fin"]
            )

            fig.update_traces(textposition='top center')
            fig.update_layout(
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,
                    xanchor="center",
                    x=0.5
                )
            )

            with col1:
                grupo_seleccionado = st.selectbox("Suministro por grupo", df_lect["Grupo"].unique(), key="selectGrupo")
                grupo_info = df_lect[df_lect["Grupo"] == grupo_seleccionado].iloc[0]
                fecha_inicio = grupo_info["inicio"]
                fecha_fin = grupo_info["fin"]
                st.write(grupo_info)
                st.write(fecha_inicio)
                st.write(fecha_fin)

                df_filtrado_suministros = df_actual[
                    (df_actual["fechaEjecucion"] >= fecha_inicio) &
                    (df_actual["fechaEjecucion"] <= fecha_fin)
                ]

                # Mostrar resultados filtrados
                st.dataframe(df_filtrado_suministros, hide_index=True)


            with col2:
                st.plotly_chart(fig, use_container_width=True)
            
    def mostrar_tablero(self, periodo, periodoPrevio, ciclo, ruta):
        datos = cargar_datos(periodo, periodoPrevio, ciclo, ruta)
        grid = st.columns(4,vertical_alignment='center')

        total_actual = len(datos["actual"])
        total_anterior = len(datos["previo"])
        diferencia_total = total_actual - total_anterior

        with grid[0]:
            with st.container(border=True):
                st.metric("Total de Suministros 🤳🏻", value=total_actual, delta=diferencia_total)

        with grid[1]:
            with st.container(border=True):
                carga_actual = datos["carga_actual"]['carga'].sum()
                carga_prev = datos["carga_previo"]['carga'].sum()
                val_actual = round(carga_actual * 100 / len(datos["carga_actual"]), 2)
                val_prev = round(carga_prev * 100 / len(datos["carga_previo"]), 2)
                df = datos["carga_actual"]
                self.mostrar_metrica(
                    "% Carga Laboral 📦", 
                    val_actual, 
                    val_prev, 
                    delta_color="inverse", 
                    detalles=df[df['carga'] == True], 
                    dfCompleto = datos["actual"]
                )

        with grid[2]:
            with st.container(border=True):
                escala_actual = (datos["escala_actual"]['apariciones_todos_lecturadores'] > 1).sum()
                escala_previo = (datos["escala_previo"]['apariciones_todos_lecturadores'] > 1).sum()
                val_actual = round(escala_actual * 100 / len(datos["escala_actual"]), 2)
                val_prev = round(escala_previo * 100 / len(datos["escala_previo"]), 2)
                df = datos["escala_actual"]
                self.mostrar_metrica(
                    "% Rutas con varios lecturadores 👥",
                    val_actual, 
                    val_prev, 
                    delta_color="inverse", 
                    detalles=df[df['apariciones_todos_lecturadores'] > 1], 
                    dfCompleto = datos["actual"]
                )

        with grid[3]:
            with st.container(border=True):
                escala_actual = (datos["escala_actual"]['apariciones_mismo_lecturador'] > 1).sum()
                escala_previo = (datos["escala_previo"]['apariciones_mismo_lecturador'] > 1).sum()
                val_actual = round(escala_actual * 100 / len(datos["escala_actual"]), 2)
                val_prev = round(escala_previo * 100 / len(datos["escala_previo"]), 2)
                df = datos["escala_actual"]
                self.mostrar_metrica(
                    "% Ejecucion de ruta anómala 😵‍💫",
                    val_actual, 
                    val_prev, 
                    delta_color="inverse", 
                    detalles=df[df['apariciones_mismo_lecturador'] > 1], 
                    dfCompleto = datos["actual"]
                )

    def view(self, periodo, periodoPrevio, ciclo, ruta):
        if 'vista_actual' in st.session_state:
            self.vista_detalles(st.session_state.df_detalles, st.session_state.vista_actual, st.session_state.df_actual, periodo, ciclo, ruta)

        else:
            self.mostrar_tablero(periodo, periodoPrevio, ciclo, ruta)

            # with grid[3]:
            #     with st.container(border=True):
            #         escala_actual = (dfEscaladoRutaActual['apariciones_mismo_lecturador'] > 1).sum()
            #         escala_anterior = (dfEscaladoRutaAnterior['apariciones_mismo_lecturador'] > 1).sum()
            #         porcentajeEscalaActual = escala_actual * 100 / len(dfEscaladoRutaActual)
            #         porcentajeEscalaAnterior = escala_anterior * 100 / len(dfEscaladoRutaAnterior)

            #         valorActual = round(porcentajeEscalaActual, 2)
            #         valorAnterior = round(porcentajeEscalaAnterior, 2)
            #         diferencia = round(valorActual - valorAnterior, 2)

            #         col1, col2 = st.columns([4, 1],vertical_alignment='center')
            #         col1.metric(label='% Ejecucion de ruta anómala 😵‍💫', value=f'{valorActual}%', delta=f'{diferencia}%', delta_color='inverse')
            #         if col2.button('👁', key='btn_anomalo', type='primary'):
            #             st.session_state.vista_actual = 'anomalo'
            #             st.rerun()

            # with grid[0]:
            #     with st.container(border=True):
            #         cronograma_actual = dfActual['cronograma'].sum()
            #         cronograma_anterior = dfAnterior['cronograma'].sum()
            #         porcentajeCronogramaActual = cronograma_actual * 100 / total_actual
            #         porcentajeCronogramaAnterior = cronograma_anterior * 100 / total_anterior

            #         valorActual = round(porcentajeCronogramaActual, 2)
            #         valorAnterior = round(porcentajeCronogramaAnterior, 2)
            #         diferencia = round(valorActual - valorAnterior, 2)

            #         col1, col2 = st.columns([4, 1],vertical_alignment='center')
            #         # col2.button(label='👁', type='primary', key='')
            #         col1.metric(label='% Cumplimiento de cronograma 📅', value=f'{valorActual}%', delta=f'{diferencia}%')
            # start_time = time.time()
            # end_time = time.time() 
            # elapsed_time = end_time - start_time
            # st.write(f"⏳ Tiempo de ejecución: {elapsed_time:.4f} segundos")

            # with grid[1]:
            #     with st.container(border=True):
            #         ejecucion_actual = (dfActual['masDiasLectura'] == False).sum()
            #         ejecucion_anterior = (dfAnterior['masDiasLectura'] == False).sum()

            #         porcentaje_actual = round(ejecucion_actual * 100 / total_actual, 2)
            #         porcentaje_anterior = round(ejecucion_anterior * 100 / total_anterior, 2)

            #         diferencia = round(porcentaje_actual - porcentaje_anterior, 2)

            #         col1, col2 = st.columns([4, 1],vertical_alignment='center')
            #         # col2.button(label='👁', type='primary', key='')
            #         col1.metric(
            #             label='Lecturas completadas en un día 🎯',
            #             value=f'{porcentaje_actual}%',
            #             delta=f'{diferencia}%'
            #         )
     
            # with grid[2]:
            #     with st.container(border=True):
            #         sin_foto_actual = (dfFotoLecturaActual['indicador_foto'] > 2).sum()
            #         sin_foto_anterior = (dfFotoLecturaAnterior['indicador_foto'] > 2).sum()

            #         porcentajeFotoActual = round(sin_foto_actual * 100 / len(dfFotoLecturaActual), 2)
            #         porcentajeFotoAnterior = round(sin_foto_anterior * 100 / len(dfFotoLecturaAnterior), 2)
            #         diferencia = round(porcentajeFotoActual - porcentajeFotoAnterior, 2)

            #         col1, col2 = st.columns([4, 1],vertical_alignment='center')
            #         # col2.button(label='👁', type='primary', key='')
            #         col1.metric(
            #             label='% Sin foto (más de 2 meses) 📷',
            #             value=f'{porcentajeFotoActual}%',
            #             delta=f'{diferencia}%',
            #             delta_color='inverse'
            #         )
            
            # with grid[3]:
            #     with st.container(border=True):
            #         sin_lectura_actual = (dfFotoLecturaActual['sin_lectura'] > 2).sum()
            #         sin_lectura_anterior = (dfFotoLecturaAnterior['sin_lectura'] > 2).sum()

            #         porcentajeLecturaActual = round(sin_lectura_actual * 100 / len(dfFotoLecturaActual), 2)
            #         porcentajeLecturaAnterior = round(sin_lectura_anterior * 100 / len(dfFotoLecturaAnterior), 2)
            #         diferencia = round(porcentajeLecturaActual - porcentajeLecturaAnterior, 2)

            #         col1, col2 = st.columns([4, 1],vertical_alignment='center')
            #         # col2.button(label='👁', type='primary', key='')
            #         col1.metric(
            #             label='% Sin lectura (más de 2 meses) 🚫',
            #             value=f'{porcentajeFotoActual}%',
            #             delta=f'{diferencia}%',
            #             delta_color='inverse'
            #         )

            # with grid[0]:
            #     with st.container(border=True):
            #         fueraRuta_actual = dfActual['fueraRuta'].sum()
            #         fueraRuta_anterior = dfAnterior['fueraRuta'].sum()
            #         porcentajefueraRutaActual = fueraRuta_actual * 100 / total_actual
            #         porcentajefueraRutaAnterior = fueraRuta_anterior * 100 / total_anterior

            #         valorActual = round(porcentajefueraRutaActual, 2)
            #         valorAnterior = round(porcentajefueraRutaAnterior, 2)
            #         diferencia = round(valorActual - valorAnterior, 2)

            #         col1, col2 = st.columns([4, 1],vertical_alignment='center')
            #         # col2.button(label='👁', type='primary', key='')
            #         col1.metric(label='% Fuera de Ruta 🗾', value=f'{valorActual}%', delta=f'{diferencia}%', delta_color='inverse')

            # with grid[1]:
            #     with st.container(border=True):
            #         sin_bandera_actual = ((dfActual['banderaAmarilla'] == False) & (dfActual['banderaRoja'] == False)).sum()
            #         sin_bandera_anterior = ((dfAnterior['banderaAmarilla'] == False) & (dfAnterior['banderaRoja'] == False)).sum()

            #         porcentajeActual = round(sin_bandera_actual * 100 / total_actual, 2)
            #         porcentajeAnterior = round(sin_bandera_anterior * 100 / total_anterior, 2)
            #         diferencia = round(porcentajeActual - porcentajeAnterior, 2)

            #         col1, col2 = st.columns([4, 1],vertical_alignment='center')
            #         # col2.button(label='👁', type='primary', key='')
            #         col1.metric(
            #             label='% Lectura en ubicación exacta 📌',
            #             value=f'{porcentajeActual}%',
            #             delta=f'{diferencia}%'
            #         )

            # with grid[2]:
            #     with st.container(border=True):
            #         estimado_actual = dfActual['estimado'].sum()
            #         estimado_anterior = dfAnterior['estimado'].sum()
            #         porcentajeestimadoActual = estimado_actual * 100 / total_actual
            #         porcentajeestimadoAnterior = estimado_anterior * 100 / total_anterior

            #         valorActual = round(porcentajeestimadoActual, 2)
            #         valorAnterior = round(porcentajeestimadoAnterior, 2)
            #         diferencia = round(valorActual - valorAnterior, 2)

            #         col1, col2 = st.columns([4, 1],vertical_alignment='center')
            #         # col2.button(label='👁', type='primary', key='')
            #         col1.metric(label='% de Estimados ✍🏻', value=f'{valorActual}%', delta=f'{diferencia}%', delta_color='inverse')

            # with grid[3]:
            #     with st.container(border=True):
            #         acumulado_actual = dfActual['acumulado'].sum()
            #         acumulado_anterior = dfAnterior['acumulado'].sum()
            #         porcentajeacumuladoActual = acumulado_actual * 100 / total_actual
            #         porcentajeacumuladoAnterior = acumulado_anterior * 100 / total_anterior

            #         valorActual = round(porcentajeacumuladoActual, 2)
            #         valorAnterior = round(porcentajeacumuladoAnterior, 2)
            #         diferencia = round(valorActual - valorAnterior, 2)

            #         col1, col2 = st.columns([4, 1],vertical_alignment='center')
            #         # col2.button(label='👁', type='primary', key='')
            #         col1.metric(label='% de Acumulados 📭', value=f'{valorActual}%', delta=f'{diferencia}%', delta_color='inverse')

            # with grid[0]:
            #     with st.container(border=True):
            #         refacturar_act = (dfActual['kwRefacturar'][dfActual['kwRefacturar'] > 0]).sum()
            #         refacturar_ant = (dfAnterior['kwRefacturar'][dfAnterior['kwRefacturar'] > 0]).sum()

            #         refacturar_act = round(refacturar_act, 2)
            #         refacturar_ant = round(refacturar_ant, 2)
            #         diferencia = round(refacturar_act - refacturar_ant, 2)

            #         col1, col2 = st.columns([4, 1],vertical_alignment='center')
            #         # col2.button(label='👁', type='primary', key='')
            #         col1.metric(
            #             label='Total kW a refacturar 🔄',
            #             value=f'{refacturar_act}',
            #             delta=f'{diferencia}',
            #             delta_color='inverse'
            #         )

            # with grid[1]:
            #     with st.container(border=True):
            #         inconsistentes_act = dfActual['observacionFacturacion'].notna() & (dfActual['observacionFacturacion'].str.strip() != '')
            #         inconsistentes_ant = dfAnterior['observacionFacturacion'].notna() & (dfAnterior['observacionFacturacion'].str.strip() != '')

            #         inconsistentes_act = inconsistentes_act.sum()
            #         inconsistentes_ant = inconsistentes_ant.sum()

            #         inconsistentes_act = round(inconsistentes_act, 2)
            #         inconsistentes_ant = round(inconsistentes_ant, 2)
            #         diferencia = round(inconsistentes_act - inconsistentes_ant, 2)

            #         col1, col2 = st.columns([4, 1],vertical_alignment='center')
            #         # col2.button(label='👁', type='primary', key='')
            #         col1.metric(
            #             label='Lecturas inconsistentes 🧐',
            #             value=f'{inconsistentes_act}',
            #             delta=f'{diferencia}',
            #             delta_color='inverse'
            #         )

            # with grid[2]:
            #     with st.container(border=True):
            #         observacion_sin_foto_act = (dfActual['observacionSinFoto']).sum()
            #         observacion_sin_foto_ant = (dfAnterior['observacionSinFoto']).sum()

            #         observacion_sin_foto_act = round(observacion_sin_foto_act, 2)
            #         observacion_sin_foto_ant = round(observacion_sin_foto_ant, 2)
            #         diferencia = round(observacion_sin_foto_act - observacion_sin_foto_ant, 2)

            #         col1, col2 = st.columns([4, 1],vertical_alignment='center')
            #         # col2.button(label='👁', type='primary', key='')
            #         col1.metric(
            #             label='Observacion sin foto 👀',
            #             value=f'{observacion_sin_foto_act}',
            #             delta=f'{diferencia}',
            #             delta_color='inverse'
            #         )

            # with grid[3]:
                # with st.container(border=True):
                #     debe_relectura_act = (dfActual['debeRelecturarse']).sum()
                #     debe_relectura_ant = (dfAnterior['debeRelecturarse']).sum()

                #     debe_relectura_act = round(debe_relectura_act, 2)
                #     debe_relectura_ant = round(debe_relectura_ant, 2)
                #     diferencia = round(debe_relectura_act - debe_relectura_ant, 2)

                #     col1, col2 = st.columns([4, 1],vertical_alignment='center')
                #     # col2.button(label='👁', type='primary', key='')
                #     col1.metric(
                #         label='Relecturas 🔃',
                #         value=f'{debe_relectura_act}',
                #         delta=f'{diferencia}',
                #         delta_color='inverse'
                #     )