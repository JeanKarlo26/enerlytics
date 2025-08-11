import streamlit as st
import pandas as pd
from views.cargar import CargarArchivosView
from controllers.auth import Auth
from controllers.dashboard import DashBoard
import plotly.express as px
from itertools import chain
from datetime import datetime, timedelta
from controllers.conection import MongoDBConnection
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial import ConvexHull
import numpy as np
from shapely.geometry import Point, Polygon
from scipy.stats import gaussian_kde

ciclos_diccionario = {
    '6149 - Ciclo 08 Huánuco': 7,
    '6698 - Ciclo 13.08 Huánuco': 7,
    '6705 - Ciclo 14.08 Huánuco': 7,
    '6713 - Ciclo 15.08 Huánuco': 7,
    '6150 - Ciclo 09 Huánuco': 6,
    '6699 - Ciclo 13.09 Huánuco': 6,
    '6706 - Ciclo 14.09 Huánuco': 6,
    '6714 - Ciclo 15.09 Huánuco': 6,
    '6151 - Ciclo 10 Huánuco': 5,
    '6692 - Ciclo 11.10 Huánuco': 5,
    '6695 - Ciclo 12.10 Huánuco': 5,
    '6700 - Ciclo 13.10 Huánuco': 5,
    '6707 - Ciclo 14.10 Huánuco': 5,
    '6715 - Ciclo 15.10 Huánuco': 5,
    '6153 - Ciclo 11 Huánuco': 4,
    '6696 - Ciclo 12.11 Huánuco': 4,
    '6701 - Ciclo 13.11 Huánuco': 4,
    '6708 - Ciclo 14.11 Huánuco': 4,
    '6716 - Ciclo 15.11 Huánuco': 4,
    '6157 - Ciclo 12 Huánuco': 3,
    '6702 - Ciclo 13.12 Huánuco': 3,
    '6709 - Ciclo 14.12 Huánuco': 3,
    '6717 - Ciclo 15.12 Huánuco': 3,
    '6162 - Ciclo 13 Huánuco': 2,
    '6710 - Ciclo 14.13 Huánuco': 2,
    '6718 - Ciclo 15.13 Huánuco': 2,
    '6163 - Ciclo 14 Huánuco': 1,
    '6719 - Ciclo 15.14 Huánuco': 1,
    '6169 - Ciclo 15 Huánuco': 0
}
cargarAchivos = CargarArchivosView()
dashboard = DashBoard()
margen = 310 / 111320

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
    
def getDiaCorrecto(row):
        ciclo = row['ciclo']
        pfactura = row['periodo']
        
        pfactura_str = str(pfactura)
        anio = int(pfactura_str[:4])
        mes = int(pfactura_str[4:])
        if mes == 12:
            ultimo_dia_mes = 31
        else:
            ultimo_dia_mes = (datetime(anio, mes+1, 1) - timedelta(days=1)).day
        
        # Calcular el día correcto de ejecución según el diccionario
        dias_resto = ciclos_diccionario[ciclo]

        return ultimo_dia_mes - dias_resto

def obtener_motivo(row):
    motivos = []

    if row["observacionFacturacion"] == "Estimacion de Consumo Manual":
        motivos.append("Estimación en facturación")

    if pd.isna(row["lecturaSigof"]) or str(row["lecturaSigof"]).strip() == "":
        motivos.append("Sin lectura en campo")

    if row["banderaRoja"]:
        motivos.append("Desvío de ubicación")

    return " - ".join(motivos) if motivos else "Sin motivo registrado"

class DashboardView:
    def __init__(self):
        self.authController = Auth()
        self.dashboard = DashBoard()
        self.conexion = MongoDBConnection()
        self.collectionLimiteRuta = self.conexion.get_collection('tblLimiteRuta')
        self.dfRectangulo = pd.DataFrame(list(self.collectionLimiteRuta.find({'estado': 1})))
    
    def mostrar_metrica(self, label, valor_actual, valor_anterior, delta_color=None, detalles=None, dfCompleto=None):
        delta = round(valor_actual - valor_anterior, 2)
        col1, col2 = st.columns([4, 1])
        col1.metric(label=label, value=f"{valor_actual}%", delta=f"{delta}%", delta_color=delta_color)
        if col2.button('👁', key=f'btn_{label}'):
            # if label == '% Carga Laboral 📦':
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
            col1, col2 = st.columns(2)
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
            with col2:
                lista_rutas = df_grafico[df_grafico['apariciones_mismo_lecturador'] > 1]
                rutas_grupos = lista_rutas[['_id', 'ruta', 'grupo']].groupby('ruta')['grupo'].apply(list).reset_index()
                grupos_unicos = list(set(chain.from_iterable(rutas_grupos['grupo'])))

                if len(lista_rutas) > 0:
                    st.markdown("### 🚨 Rutas Anómalas y sus Grupos")
                    resumen = []
                    for grupo in sorted(grupos_unicos):
                        grupo_info = df_lect[df_lect["Grupo"] == grupo].iloc[0]
                        fecha_inicio = grupo_info["inicio"]
                        fecha_fin = grupo_info["fin"]
                        lecturista = grupo_info["lecturista"]

                        # Filtrar suministros
                        df_filtrado = df_actual[
                            (df_actual["fechaEjecucion"] >= fecha_inicio) &
                            (df_actual["fechaEjecucion"] <= fecha_fin) &
                            (df_actual["lecturista"] == lecturista)
                        ]

                        resumen.append({
                            "Grupo": grupo,
                            "Total Suministros": len(df_filtrado),
                            "Suministros": df_filtrado[["suministro"]]
                        })

                    for item in resumen:
                        with st.expander(f"Grupo {item['Grupo']} — {item['Total Suministros']} registros"):
                            st.dataframe(item["Suministros"], use_container_width=True, hide_index=True)

                else:
                    st.info('No hay Rutas anómalas')
                
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
                    orientation="v",
                    yanchor="bottom",
                    y=5,
                    xanchor="center",
                    x=0
                )
            )
            st.plotly_chart(fig, use_container_width=True)
            
        if label == '% Lecturas correctas segun cronograma ⏱':
            col1, col2 = st.columns(2)

            df_actual['diaLectura'] = df_actual['fechaEjecucion'].dt.day
            df_actual['diaCorrecto'] = df_actual.apply(getDiaCorrecto,axis=1)
            df_actual['diferenciaDias'] = abs(df_actual['diaLectura'] - df_actual['diaCorrecto'])

            with col1:
                cumplimiento_df = df_actual["cronograma"].value_counts().reset_index()
                cumplimiento_df.columns = ["Estado", "Cantidad"]
                cumplimiento_df["Estado"] = cumplimiento_df["Estado"].map({True: "✅ Cumplido", False: "❌ No Cumplido"})

                fig = px.pie(
                    cumplimiento_df,
                    names="Estado",
                    values="Cantidad",
                    hole=0.4,
                    color="Estado",
                    color_discrete_map={"✅ Cumplido": "#2ECC71", "❌ No Cumplido": "#E74C3C"},
                    title="Cumplimiento de Cronograma"
                )
            
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                resumen = df_actual.groupby(["ruta", "cronograma"]).size().unstack(fill_value=0).reset_index()
                resumen.columns = ["Ruta", "No Cumplido", "Cumplido"]
                resumen["% Cumplido"] = (resumen["Cumplido"] / (resumen["Cumplido"] + resumen["No Cumplido"]) * 100).round(1)
                st.text('Lista de rutas con incumplimiento')
                st.dataframe(resumen[resumen["% Cumplido"] < 100][['Ruta', '% Cumplido']], hide_index=True)

            lecturistas = df_actual["lecturista"].unique()
            selectLecturador = st.selectbox('Lecturador:', lecturistas)

            tab1, tab2, tab3 = st.tabs(["Curva de cumplimiento por ruta", "Resumen de cumplimiento por ruta", "Suministro por ruta "])

            with tab2:
                df_por_lecturista = df_actual[df_actual['lecturista'] == selectLecturador].copy()
                resumen = df_por_lecturista.groupby(["ruta", "cronograma"]).size().unstack(fill_value=0).reset_index()
                for estado in [True, False]:
                    if estado not in resumen.columns:
                        resumen[estado] = 0

                resumen.columns = ["Ruta", "No Cumplido", "Cumplido"]
                resumen["% Cumplido"] = (
                    resumen.get("Cumplido", 0) / (resumen.get("Cumplido", 0) + resumen.get("No Cumplido", 0)) * 100
                ).round(1)
                st.dataframe(resumen, hide_index=True)

            with tab1:
                agrupado = df_por_lecturista.groupby("ruta")["cronograma"].agg(["sum", "count"]).reset_index()
                agrupado["% Cumplimiento"] = (agrupado["sum"] / agrupado["count"] * 100).round(1)
                agrupado = agrupado.sort_values("% Cumplimiento")

                fig = px.line(
                    agrupado,
                    x="ruta",
                    y="% Cumplimiento",
                    markers=True,
                    line_shape="spline",
                    title="Curva de Cumplimiento por Ruta",
                )

                fig.update_traces(line_color="#2ECC71", marker=dict(color="#1B4F72", size=8))
                fig.update_layout(xaxis_title="Ruta", yaxis_title="Cumplimiento (%)")
                st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                col3, col4 = st.columns(2)
                rutas = df_por_lecturista["ruta"].unique()
                with col3:
                    selectRuta = st.selectbox('Ruta:', rutas)
                with col4:
                    radioEstado = st.radio('Estado',['Todos', 'Cumplido', 'No Cumplido'])
                if radioEstado == 'Todos':
                    df_por_lecturista_ruta = df_por_lecturista[df_por_lecturista['ruta'] == selectRuta].copy()
                elif radioEstado == 'Cumplido':
                    df_por_lecturista_ruta = df_por_lecturista[(df_por_lecturista['ruta'] == selectRuta) & (df_por_lecturista['cronograma'] == True)].copy()
                else:
                    df_por_lecturista_ruta = df_por_lecturista[(df_por_lecturista['ruta'] == selectRuta) & (df_por_lecturista['cronograma'] == False)].copy()

                df_por_lecturista_ruta.rename(columns={'cronograma': 'Cumplimiento', 'diaLectura': 'Día Lecturado','diaCorrecto':'Día Correcto', 'diferenciaDias':'Desfase (dias)'}, inplace=True)
                st.dataframe(df_por_lecturista_ruta[['suministro','Cumplimiento','Día Lecturado','Día Correcto','Desfase (dias)']], hide_index=True)

        if label == '% Lecturas completadas en un día 🎯':
            
            ciclos = df_actual["ciclo"].unique()
            selectciclo = st.selectbox('Ciclo:', sorted(ciclos))
            df_actual_nuevo = df_actual[df_actual['ciclo'] == selectciclo].copy()

            df_actual_nuevo['diaLectura'] = df_actual_nuevo['fechaEjecucion'].dt.day
            df_actual_nuevo['diaCorrecto'] = df_actual_nuevo.apply(getDiaCorrecto,axis=1)
            df_actual_nuevo['diferenciaDias'] = abs(df_actual_nuevo['diaLectura'] - df_actual_nuevo['diaCorrecto'])
            
            df_actual_nuevo["masDiasLectura"] = df_actual_nuevo["masDiasLectura"].astype(bool)
            df_actual_nuevo["estadoLectura"] = df_actual_nuevo["masDiasLectura"].map({False: "✅ En un día", True: "⏳ Más días"})
            df_barra = df_actual_nuevo.groupby(["ruta", "estadoLectura"]).size().unstack(fill_value=0)
            df_barra = df_actual_nuevo.groupby(["ruta", "estadoLectura"]).size().unstack(fill_value=0)

            fig = px.bar(
                df_barra.reset_index(),
                x="ruta",
                y=["✅ En un día", "⏳ Más días"],
                color_discrete_map={"✅ En un día": "#2ECC71", "⏳ Más días": "#E74C3C"},
                barmode="stack",
                title="Rutas: cumplimiento en un solo día vs dispersión"
            )
            st.plotly_chart(fig, use_container_width=True)
            col1, col2 = st.columns([1,2])

            with col1:
                ejecucionRadio = st.radio('Estado:',["Todos","✅ En un día","⏳ Más días"],horizontal=True)

            with col2:
                if ejecucionRadio == 'Todos':
                    rutas = df_actual_nuevo['ruta'].unique()
                else:
                    rutas = df_actual_nuevo[df_actual_nuevo['estadoLectura'] == ejecucionRadio]['ruta'].unique()

                selectRuta = st.selectbox('Ruta: ', rutas)
            
            with col1:
                df_actual_nuevo = df_actual_nuevo[df_actual_nuevo['ruta'] == selectRuta]
                df_estado = df_actual_nuevo["estadoLectura"].value_counts().reset_index()
                df_estado.columns = ["Estado Ejecucion", "Cantidad"]
                fig = px.pie(
                    df_estado,
                    names="Estado Ejecucion",
                    values="Cantidad",
                    hole=0.4,
                    color="Estado Ejecucion",
                    color_discrete_map={"✅ En un día": "#2ECC71", "⏳ Más días": "#E74C3C"},
                    title=f"Ejecucion de la ruta"
                )
                st.plotly_chart(fig, use_container_width=True)
            # with col2:
            #     
            
            # filtroEstado = False if ejecucionRadio == "✅ En un día" else True
            # df_for_rutas = df_actual_nuevo[df_actual_nuevo['estadoLectura'] == ejecucionRadio]
            
            with col2:
                fecha_min = df_actual_nuevo["fechaEjecucion"].min()
                fecha_max = df_actual_nuevo["fechaEjecucion"].max()
                dias_entre_lecturas = (fecha_max - fecha_min).days
                col3, col4 = st.columns(2)
                with col3:
                    st.write(f'Total de días de lectura: {dias_entre_lecturas+1}')
                # st.write(f'Dia correcto de lectura: {ciclos_diccionario[selectciclo]}')

                df_actual_nuevo["fecha"] = df_actual_nuevo["fechaEjecucion"].dt.date
                fechas_disponibles = sorted(df_actual_nuevo["fecha"].unique())
                with col4:
                    fecha_seleccionada = st.radio("Selecciona una fecha", fechas_disponibles, horizontal=True)
                df_filtrado = df_actual_nuevo[df_actual_nuevo["fecha"] == fecha_seleccionada]
                st.dataframe(df_filtrado[["suministro", 'diaCorrecto']], hide_index=True)

        if label == '% Fuera de Ruta 🗾':
            col1, col2 = st.columns(2)
            ciclos = df_actual["ciclo"].unique()
            with col1:
                selectciclo = st.selectbox('Ciclo:', sorted(ciclos))
            df_actual_nuevo = df_actual[df_actual['ciclo'] == selectciclo].copy()

            rutas = df_actual_nuevo["ruta"].unique()
            with col1:
                selectRuta = st.selectbox('Ruta:', sorted(rutas))
            df_actual_nuevo = df_actual_nuevo[df_actual_nuevo['ruta'] == selectRuta].copy()      

            limites_df = self.dfRectangulo[self.dfRectangulo['ruta'] == selectRuta].copy()

            if not limites_df.empty:
                min_lat = limites_df["min_lat"]
                max_lat = limites_df["max_lat"]
                min_lon = limites_df["min_lon"]
                max_lon = limites_df["max_lon"]

                fig, ax = plt.subplots(figsize=(10, 7))
                ax.scatter(df_actual_nuevo['longitud'], df_actual_nuevo['latitud'], c='blue', label='Suministros')
                ax.scatter(df_actual_nuevo[df_actual_nuevo['fueraRuta']]['longitud'], df_actual_nuevo[df_actual_nuevo['fueraRuta']]['latitud'], c='red', label='Fuera de Ruta')
                ax.plot([min_lon, max_lon, max_lon, min_lon, min_lon], [min_lat, min_lat, max_lat, max_lat, min_lat], color='green', label='Rectángulo Limitante')
                ax.set_xlabel('Longitud')
                ax.set_ylabel('Latitud')
                ax.legend()
                with col2:
                    st.write('Coordenadas limitantes y puntos fuera de ruta')
                    st.pyplot(fig)
                with col1:
                    st.metric(
                        '# Suministros fuera de ruta:',
                        len(df_actual_nuevo[df_actual_nuevo['fueraRuta']]),
                        delta=f'Total de suministros: {len(df_actual_nuevo)}',
                        delta_color='off'
                    )

            else:
                st.error('No encontramos límites para la ruta actual', icon="🚨")
                if st.button('Deseas agregarla?'):
                    # Calcular el IQR para latitud y longitud para identificar valores anómalos
                    Q1_lat = df_actual_nuevo['latitud'].quantile(0.25)
                    Q3_lat = df_actual_nuevo['latitud'].quantile(0.75)
                    IQR_lat = Q3_lat - Q1_lat

                    Q1_lon = df_actual_nuevo['longitud'].quantile(0.25)
                    Q3_lon = df_actual_nuevo['longitud'].quantile(0.75)
                    IQR_lon = Q3_lon - Q1_lon

                    # Definir límites para considerar valores no anómalos
                    limite_inf_lat = Q1_lat - 1.5 * IQR_lat
                    limite_sup_lat = Q3_lat + 1.5 * IQR_lat
                    limite_inf_lon = Q1_lon - 1.5 * IQR_lon
                    limite_sup_lon = Q3_lon + 1.5 * IQR_lon

                    # Excluir valores anómalos
                    ruta_df_filtrada = df_actual_nuevo[
                        (df_actual_nuevo['latitud'] >= limite_inf_lat) & (df_actual_nuevo['latitud'] <= limite_sup_lat) &
                        (df_actual_nuevo['longitud'] >= limite_inf_lon) & (df_actual_nuevo['longitud'] <= limite_sup_lon)
                    ]

                    # Calcular las coordenadas mínimas y máximas con el margen
                    min_lat = ruta_df_filtrada['latitud'].min() - margen
                    max_lat = ruta_df_filtrada['latitud'].max() + margen
                    min_lon = ruta_df_filtrada['longitud'].min() - margen
                    max_lon = ruta_df_filtrada['longitud'].max() + margen

                    # Guardar los resultados en MongoDB
                    rectangulo_envolvente = {
                        "ruta": selectRuta,
                        "min_lat": min_lat,
                        "max_lat": max_lat,
                        "min_lon": min_lon,
                        "max_lon": max_lon,
                        "estado": 1
                    }
                    self.collectionLimiteRuta.insert_one(rectangulo_envolvente)        
                    st.write(f'Se genero limites para la ruta {selectRuta}')

            radioSuministro = st.radio('Suministros',['Fuera de ruta', 'En ruta', 'Todos'], horizontal=True)

            if radioSuministro == 'Fuera de ruta':
                df_mostrar_suministros = df_actual_nuevo[df_actual_nuevo['fueraRuta']][['suministro', 'latitud', 'longitud']]
            elif radioSuministro == 'En ruta':
                df_mostrar_suministros = df_actual_nuevo[~df_actual_nuevo['fueraRuta']][['suministro', 'latitud', 'longitud']]
            elif radioSuministro == 'Todos':
                df_mostrar_suministros = df_actual_nuevo[['suministro', 'latitud', 'longitud']]
            
            if df_mostrar_suministros.empty:
                st.warning('No se encuentras suministros con la seleccion', icon='⚠️')
            else:
                col3, col4 = st.columns(2)
                with col3:
                    st.map(df_mostrar_suministros,latitude='latitud', longitude='longitud', size=0.2)
                with col4:
                    st.dataframe(df_mostrar_suministros,hide_index=True)   

        if label =='% Sin foto (más de 3 meses) 📷':
            ciclos = df['ciclo'].unique().tolist()
            ciclos.insert(0, "-- Todos --")

            col3, col4 = st.columns([4,1])
            
            with col3:
                selectCiclos = st.selectbox('Ciclo: ', ciclos)

            if selectCiclos == '-- Todos --':
                df = df.sort_values(by='indicador_foto', ascending=False)
            else:
                df = (
                    df[df['ciclo'] == selectCiclos]
                    .sort_values(by='indicador_foto', ascending=False)
                )
            with col4:
                st.metric('Total suministros', value=len(df))
            
            df["estado"] = pd.cut(
                df["indicador_foto"],
                bins=[-1, 1, 3, float("inf")],
                labels=["Correcto ✅", "Advertencia ⚠️", "Peligro ☠️"]
            )

            fig = px.pie(
                df,
                names="estado",
                hole=0.5,
                color="estado",
                color_discrete_map={
                    "Peligro ☠️": "#fb8080",
                    "Advertencia ⚠️": "#fae9a4",
                    "Correcto ✅": "#cbfbcb"
                },
            )
            fig.update_traces(textinfo="label+percent")

            col1, col2 = st.columns(2)
            with col1:

                col3, col4, col5 = st.columns(3)
                with col3:
                    st.metric('Peligro ☠️', value=len(df[df['estado'] == 'Peligro ☠️']))
                with col4:
                    st.metric('Advertencia ⚠️', value=len(df[df['estado'] == 'Advertencia ⚠️']))
                with col5:
                    st.metric('Correcto ✅', value=len(df[df['estado'] == 'Correcto ✅']))

                st.plotly_chart(fig, use_container_width=True)

            with col2:
                estado_seleccionado = st.radio(
                    "Filtrar por estado:",
                    options=["Peligro ☠️", "Advertencia ⚠️", "Correcto ✅"],
                    horizontal=True
                )

                df_filtrado = df[df["estado"] == estado_seleccionado]
                df_filtrado.rename(columns={'indicador_foto': 'Meses sin foto'}, inplace=True)

                st.dataframe(
                    df_filtrado[['suministro','Meses sin foto']], 
                    hide_index=True
                )

        if label =='% Sin lectura (más de 3 meses) 🚫':
            ciclos = df['ciclo'].unique().tolist()
            ciclos.insert(0, "-- Todos --")

            col3, col4 = st.columns([4,1])
            
            with col3:
                selectCiclos = st.selectbox('Ciclo: ', ciclos)

            if selectCiclos == '-- Todos --':
                df = df.sort_values(by='sin_lectura', ascending=False)
            else:
                df = (
                    df[df['ciclo'] == selectCiclos]
                    .sort_values(by='sin_lectura', ascending=False)
                )
            with col4:
                st.metric('Total suministros', value=len(df))
            
            df["estado"] = pd.cut(
                df["sin_lectura"],
                bins=[-1, 1, 3, float("inf")],
                labels=["Correcto ✅", "Advertencia ⚠️", "Peligro ☠️"]
            )

            fig = px.pie(
                df,
                names="estado",
                hole=0.5,
                color="estado",
                color_discrete_map={
                    "Peligro ☠️": "#fb8080",
                    "Advertencia ⚠️": "#fae9a4",
                    "Correcto ✅": "#cbfbcb"
                },
            )
            fig.update_traces(textinfo="label+percent")

            col1, col2 = st.columns(2)
            with col1:

                col3, col4, col5 = st.columns(3)
                with col3:
                    st.metric('Peligro ☠️', value=len(df[df['estado'] == 'Peligro ☠️']))
                with col4:
                    st.metric('Advertencia ⚠️', value=len(df[df['estado'] == 'Advertencia ⚠️']))
                with col5:
                    st.metric('Correcto ✅', value=len(df[df['estado'] == 'Correcto ✅']))

                st.plotly_chart(fig, use_container_width=True)

            with col2:
                estado_seleccionado = st.radio(
                    "Filtrar por estado:",
                    options=["Peligro ☠️", "Advertencia ⚠️", "Correcto ✅"],
                    horizontal=True
                )

                df_filtrado = df[df["estado"] == estado_seleccionado]
                df_filtrado.rename(columns={'sin_lectura': 'Meses sin lectura'}, inplace=True)

                st.dataframe(
                    df_filtrado[['suministro','Meses sin lectura']], 
                    hide_index=True
                )

        if label == 'Relecturas 🔃':
            col1, col2 = st.columns([1,3])
            

            with col1:
                ciclos = df_actual['ciclo'].unique().tolist()
                if "-- Todos --" not in ciclos:
                    ciclos.insert(0, "-- Todos --") 
                selectCiclos = st.selectbox('Ciclo:', ciclos)

                if selectCiclos != '-- Todos --':
                    df_actual = df_actual[df_actual['ciclo'] == selectCiclos].copy()

                rutas = df_actual['ruta'].unique().tolist()
                if "-- Todos --" not in rutas:
                    rutas.insert(0, "-- Todos --") 
                selectRutas = st.selectbox('Ruta::', rutas)

                if selectRutas != '-- Todos --':
                    df_actual = df_actual[df_actual['ruta'] == selectRutas].copy()

                total_relecturados = df_actual[df_actual["relectura"] == True].shape[0]
                total_pendientes = df_actual[df_actual["debeRelecturarse"] == True].shape[0]
                st.metric("✅ Relecturados", total_relecturados)
                st.metric("⚠️ Pendientes de relectura", total_pendientes)

            df_actual = df_actual[(df_actual["relectura"] == True) | (df_actual["debeRelecturarse"] == True)]
            
            with col2:
                tab1, tab2 = st.tabs(['Estado de relecturas', 'Lista de casos'])
                with tab1:
                    df_actual["estadoRelectura"] = df_actual.apply(
                        lambda row: "Relecturado" if row["relectura"] else (
                            "Pendiente" if row["debeRelecturarse"] else "Sin incidencia"
                        ),
                        axis=1
                    )

                    conteo = df_actual["estadoRelectura"].value_counts().reset_index()
                    conteo.columns = ["Estado", "Cantidad"]

                    fig = px.pie(
                        conteo,
                        names="Estado",
                        values="Cantidad",
                        hole=0.4,
                        color="Estado",
                        color_discrete_map={
                            "Relecturado": "#2ECC71",
                            "Pendiente": "#F39C12"
                        },
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with tab2:
                    relecturaRadio = st.radio('Estado', ['Todos','Relecturados', 'Pendiente de Relectura'], horizontal=True)
                    if relecturaRadio == 'Todos':
                        df_filtrado = df_actual[['suministro', 'ruta','lecturista','observacionLectura']].copy()
                    elif relecturaRadio == 'Relecturados':
                        df_filtrado = df_actual[df_actual['relectura'] ==True][['suministro', 'ruta','lecturista','observacionLectura']].copy()
                    else:
                        df_filtrado = df_actual[df_actual['debeRelecturarse'] ==True][['suministro', 'ruta','lecturista','observacionLectura']].copy()

                    st.dataframe(df_filtrado, hide_index=True)

        if label == '% de Estimados ✍🏻':
            col1, col2 = st.columns([1,3])

            with col1:
                ciclos = df_actual['ciclo'].unique().tolist()
                if "-- Todos --" not in ciclos:
                    ciclos.insert(0, "-- Todos --") 
                selectCiclos = st.selectbox('Ciclo:', ciclos)

                if selectCiclos != '-- Todos --':
                    df_actual = df_actual[df_actual['ciclo'] == selectCiclos].copy()

                rutas = df_actual['ruta'].unique().tolist()
                if "-- Todos --" not in rutas:
                    rutas.insert(0, "-- Todos --") 
                selectRutas = st.selectbox('Ruta::', rutas)

                if selectRutas != '-- Todos --':
                    df_actual = df_actual[df_actual['ruta'] == selectRutas].copy()
                
                df_actual["estimado"] = df_actual["estimado"].astype(int)
                estimados = df_actual["estimado"].sum()
                porcentaje = (estimados / len(df_actual)) * 100

                st.metric("Lecturas estimadas", estimados)
                st.metric("Porcentaje estimado", f"{porcentaje:.2f}%")


            with col2:
                if selectCiclos == '-- Todos --':
                    df_estimado_cantidad = df_actual.groupby("ciclo")["estimado"].sum()
                    nombreTab = 'Cantidad de estimados por ciclo'
                
                elif selectRutas == '-- Todos --':
                    df_estimado_cantidad = df_actual.groupby("ruta")["estimado"].sum()
                    nombreTab = 'Cantidad de estimados por ruta'

                else:
                    nombreTab = 'Mapa de estimados'
                
                tab1, tab2, tab3 = st.tabs(["Evolucion de estimados por dia", nombreTab, "Distribución de motivos de estimación"])

                with tab1:
                    df_actual["fecha"] = df_actual["fechaEjecucion"].dt.date
                    df_fecha = df_actual.groupby("fecha")["estimado"].mean().reset_index()
                    df_fecha["% estimado"] = df_fecha["estimado"] * 100
                    st.line_chart(df_fecha.set_index("fecha")["% estimado"])

                with tab2:
                    if nombreTab != 'Mapa de estimados':
                        st.bar_chart(df_estimado_cantidad)
                    else:
                        df_map = df_actual[df_actual['estimado'] == 1][["latitud", "longitud"]]
                        st.map(df_map, latitude='latitud', longitude='longitud', size=0.5)                    

                df_actual['motivo'] = df_actual[df_actual['estimado']== 1].apply(obtener_motivo, axis=1)
                conteo_motivos = df_actual["motivo"].value_counts().reset_index()
                conteo_motivos.columns = ["Motivo", "Cantidad"]

                with tab3:
                    fig = px.pie(
                        conteo_motivos,
                        names="Motivo",
                        values="Cantidad",
                        hole=0.4,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with st.expander('📊 Lista de suministros estimados', expanded=False):
                    st.dataframe(df_actual[df_actual['estimado']== 1][['suministro','ruta','consumo', 'lecturaFinal','motivo']], hide_index=True)

        if label == '% de Acumulados 📭':
            df_actual = df_actual[df_actual['acumulado'] == True].copy()
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric('Total de acumulados', len(df_actual))

            df_acumulado = df_actual[[
                'suministro','ciclo','ruta', 'consumo', 'lecturaFinal',
                'promedio6Meses', 'consumoAnterior', 'lecturaAnterior',
                'banderaRoja','observacionFacturacion', 'distanciaMetros'
            ]]

            col1, col2 = st.columns(2, vertical_alignment='center')
            with st.container(border=True):
                with col1:
                    suministro = df_actual['suministro'].unique().tolist()
                    selectSuministro = st.selectbox('Suministro:', suministro)
                    
                    df_filtrado = df_acumulado[df_acumulado['suministro'] == selectSuministro].copy()

                    st.write(f'Ciclo: {df_filtrado['ciclo'].tolist()[0]}')
                    st.write(f'Ruta: {df_filtrado['ruta'].tolist()[0]}')
                    st.write(f'Consumo: {df_filtrado['consumo'].tolist()[0]}')
                    st.write(f'Lectura final: {df_filtrado['lecturaFinal'].tolist()[0]}')
                    st.write(f'Consumo anterior: {df_filtrado['consumoAnterior'].tolist()[0]}')
                    st.write(f'Lectura anterior: {df_filtrado['lecturaAnterior'].tolist()[0]}')
                    st.write(f'Promedio 6 meses: {df_filtrado['promedio6Meses'].tolist()[0]}')
                    st.write(f'Estado coordenadas: {round(df_filtrado['distanciaMetros'].tolist()[0],2)} metros')
                    st.write(f'Observacion: {df_filtrado['observacionFacturacion'].tolist()[0]}')

                with col2:
                    st.write("Consumo vs consumo anterior vs promedio 6 meses")
                    fig = px.bar(
                        df_filtrado,
                        x="ciclo",
                        y=["consumo", "consumoAnterior", 'promedio6Meses'],
                        barmode="group",
                        color_discrete_map={"consumo": "#3498DB", "consumoAnterior": "#2ECC71", 'promedio6Meses': "#CC2E33"}
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with st.expander('Listado completo', expanded=False):
                st.dataframe(df_acumulado, hide_index=True)

            # st.dataframe(, hide_index=True)

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
                    detalles=df, 
                    dfCompleto = datos["actual"]
                )

        with grid[0]:
            with st.container(border=True):
                cronograma_actual = datos["actual"]['cronograma'].sum()
                cronograma_anterior = datos["previo"]['cronograma'].sum()
                val_actual = round(cronograma_actual * 100 / total_actual, 2)
                val_prev = round(cronograma_anterior * 100 / total_anterior, 2)
                self.mostrar_metrica(
                    "% Lecturas correctas segun cronograma ⏱",
                    val_actual, 
                    val_prev, 
                    delta_color="normal", 
                    detalles=None, 
                    dfCompleto = datos["actual"]
                )

        with grid[1]:
            with st.container(border=True):
                ejecucion_actual = (datos["actual"]['masDiasLectura'] == False).sum()
                ejecucion_anterior = (datos["previo"]['masDiasLectura'] == False).sum()
                val_actual = round(ejecucion_actual * 100 / total_actual, 2)
                val_prev = round(ejecucion_anterior * 100 / total_anterior, 2)
                self.mostrar_metrica(
                    "% Lecturas completadas en un día 🎯",
                    val_actual, 
                    val_prev, 
                    delta_color="normal", 
                    detalles=None, 
                    dfCompleto = datos["actual"]
                )

        with grid[0]:
            with st.container(border=True):
                fueraRuta_actual = datos['actual']['fueraRuta'].sum()
                fueraRuta_anterior = datos['previo']['fueraRuta'].sum()
                val_actual = round(fueraRuta_actual * 100 / total_actual, 2)
                val_prev = round(fueraRuta_anterior * 100 / total_anterior, 2)

                self.mostrar_metrica(
                    "% Fuera de Ruta 🗾",
                    val_actual, 
                    val_prev, 
                    delta_color="inverse", 
                    detalles=None, 
                    dfCompleto = datos["actual"]
                )

        with grid[2]:
            with st.container(border=True):
                sin_foto_actual = (datos['foto_actual']['indicador_foto'] > 3).sum()
                sin_foto_anterior = (datos['foto_previo']['indicador_foto'] > 3).sum()
                val_actual = round(sin_foto_actual * 100 / len(datos['foto_actual']), 2)
                val_prev = round(sin_foto_anterior * 100 / len(datos['foto_previo']), 2)

                self.mostrar_metrica(
                    "% Sin foto (más de 3 meses) 📷",
                    val_actual, 
                    val_prev, 
                    delta_color="inverse", 
                    detalles=datos['foto_actual'], 
                    dfCompleto = datos["actual"]
                )

        with grid[3]:
            with st.container(border=True):
                sin_lectura_actual = (datos['foto_actual']['sin_lectura'] > 3).sum()
                sin_lectura_anterior = (datos['foto_previo']['sin_lectura'] > 3).sum()

                val_actual = round(sin_lectura_actual * 100 / len(datos['foto_actual']), 2)
                val_prev = round(sin_lectura_anterior * 100 / len(datos['foto_previo']), 2)

                self.mostrar_metrica(
                    "% Sin lectura (más de 3 meses) 🚫",
                    val_actual, 
                    val_prev, 
                    delta_color="inverse", 
                    detalles=datos['foto_actual'], 
                    dfCompleto = datos["actual"]
                )

        with grid[3]:
            with st.container(border=True):
                debe_relectura_act = (datos['actual']['debeRelecturarse']).sum()
                debe_relectura_ant = (datos['previo']['debeRelecturarse']).sum()

                val_actual = round(debe_relectura_act * 100 / total_actual, 2)
                val_prev = round(debe_relectura_ant * 100 / total_anterior, 2)

                self.mostrar_metrica(
                    "Relecturas 🔃",
                    val_actual, 
                    val_prev, 
                    delta_color="inverse", 
                    detalles=None, 
                    dfCompleto = datos["actual"]
                )

        with grid[2]:
            with st.container(border=True):
                estimado_actual = (datos['actual']['estimado']).sum()
                estimado_anterior = (datos['previo']['estimado']).sum()
                val_actual = round(estimado_actual * 100 / total_actual, 2)
                val_prev = round(estimado_anterior * 100 / total_anterior, 2)

                self.mostrar_metrica(
                    "% de Estimados ✍🏻",
                    val_actual, 
                    val_prev, 
                    delta_color="inverse", 
                    detalles=None, 
                    dfCompleto = datos["actual"]
                )

        with grid[1]:
            with st.container(border=True):
                acumulado_actual = (datos['actual']['acumulado']).sum()
                acumulado_anterior = (datos['previo']['acumulado']).sum()

                val_actual = round(acumulado_actual * 100 / total_actual,2)
                val_prev = round(acumulado_anterior * 100 / total_anterior,2)

                self.mostrar_metrica(
                    "% de Acumulados 📭",
                    val_actual, 
                    val_prev, 
                    delta_color="inverse", 
                    detalles=None, 
                    dfCompleto = datos["actual"]
                )

    def view(self, periodo, periodoPrevio, ciclo, ruta):
        if 'vista_actual' in st.session_state:
            self.vista_detalles(st.session_state.df_detalles, st.session_state.vista_actual, st.session_state.df_actual, periodo, ciclo, ruta)

        else:
            self.mostrar_tablero(periodo, periodoPrevio, ciclo, ruta)



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