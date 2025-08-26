import streamlit as st
import pandas as pd
from controllers.conection import MongoDBConnection
import plotly.express as px



class AnalisisTemporal:
    def __init__(self):
        self.conexion = MongoDBConnection()
        self.collectionResultados = self.conexion.get_collection('tblResultadoFinal')

    def view(self, listaPeriodos, listaRutas):
        dfCompleto = pd.DataFrame(list(
            self.collectionResultados.find({
                'periodo': {'$in': listaPeriodos},
                'ruta': {'$in': listaRutas}
            })
        ))

        listTipo =[
            'Total de suministros', 
            '% Lecturas correctas segun cronograma',
            '% Lecturas completadas en un día 🎯',
            '% Fuera de Ruta 🗾',
            'Relecturas 🔃',
            '% de Estimados ✍🏻',
            '% de Acumulados 📭',
            'Total kW a refacturar 🔄',
            'Lecturas inconsistentes 🧐',
            '% Lectura en ubicación inexacta 📌',
            'Observaciones 👀'
        ]
        tipo = st.selectbox('Dimension a evaluar', listTipo)

        self.graficar(dfCompleto, tipo)
    
    def graficar(self, df, tipo):
        if tipo == 'Total de suministros':
            totales_por_periodo = df.groupby('periodo').size().reset_index(name='total')

            min_valor = totales_por_periodo['total'].min()
            margen = int(min_valor * 0.9)

            fig = px.line(
                totales_por_periodo,
                x='periodo',
                y='total',
                markers=True,
                title='Total de suministros por periodo'
            )

            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=totales_por_periodo['periodo'].tolist()
                ),
                yaxis=dict(
                    range=[margen, totales_por_periodo['total'].max()]
                ),
                template='plotly_white'
            )

            st.plotly_chart(fig, use_container_width=True)
        
        if tipo == '% Lecturas correctas segun cronograma':
            resumen = df.groupby('periodo').agg({
                'cronograma': 'sum',
                'suministro': 'count'
            }).reset_index().rename(columns={'suministro': 'total_suministros'})

            resumen['% lecturas correctas'] = round(
                resumen['cronograma'] * 100 / resumen['total_suministros'], 2
            )

            min_valor = resumen['% lecturas correctas'].min()
            margen = min_valor * 0.9

            fig = px.line(
                resumen,
                x='periodo',
                y='% lecturas correctas',
                markers=True,
                title='% Lecturas correctas según cronograma'
            )

            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=resumen['periodo'].tolist()
                ),
                yaxis=dict(
                    range=[margen, resumen['% lecturas correctas'].max() * 1.05]
                ),
                template='plotly_white'
            )

            st.plotly_chart(fig, use_container_width=True)

        if tipo == '% Lecturas completadas en un día 🎯':
            df['ejecucion_ok'] = df['masDiasLectura'] == False

            resumen = df.groupby('periodo').agg(
                total_registros=('masDiasLectura', 'count'),
                ejecuciones_sin_retraso=('ejecucion_ok', 'sum')
            ).reset_index()

            resumen['% ejecución sin retraso'] = round(
                resumen['ejecuciones_sin_retraso'] * 100 / resumen['total_registros'], 2
            )

            min_valor = resumen['% ejecución sin retraso'].min()
            margen = min_valor * 0.9

            fig = px.line(
                resumen,
                x='periodo',
                y='% ejecución sin retraso',
                markers=True,
                title='% Lecturas completadas en un día 🎯'
            )

            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=resumen['periodo'].tolist()
                ),
                yaxis=dict(
                    range=[margen, resumen['% ejecución sin retraso'].max() * 1.05]
                ),
                template='plotly_white'
            )

            st.plotly_chart(fig, use_container_width=True)

        if tipo == '% Fuera de Ruta 🗾':
            df['fueraRuta'] = df['fueraRuta'].astype(bool)

            resumen = df.groupby('periodo').agg(
                total_registros=('fueraRuta', 'count'),
                fuera_ruta=('fueraRuta', 'sum')
            ).reset_index()

            resumen['% fuera de ruta'] = round(
                resumen['fuera_ruta'] * 100 / resumen['total_registros'], 2
            )

            min_valor = resumen['% fuera de ruta'].min()
            margen = min_valor * 0.9

            fig = px.line(
                resumen,
                x='periodo',
                y='% fuera de ruta',
                markers=True,
                title='% Fuera de Ruta 🗾'
            )

            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=resumen['periodo'].tolist()
                ),
                yaxis=dict(
                    range=[margen, resumen['% fuera de ruta'].max() * 1.05]
                ),
                template='plotly_white'
            )

            st.plotly_chart(fig, use_container_width=True)

        if tipo == 'Relecturas 🔃':
            df['debeRelecturarse'] = df['debeRelecturarse'].astype(bool)

            resumen = df.groupby('periodo').agg(
                total_registros=('debeRelecturarse', 'count'),
                relecturas=('debeRelecturarse', 'sum')
            ).reset_index()

            resumen['% relecturas necesarias'] = round(
                resumen['relecturas'] * 100 / resumen['total_registros'], 2
            )

            min_valor = resumen['% relecturas necesarias'].min()
            margen = min_valor * 0.9

            fig = px.line(
                resumen,
                x='periodo',
                y='% relecturas necesarias',
                markers=True,
                title='Relecturas 🔃'
            )

            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=resumen['periodo'].tolist()
                ),
                yaxis=dict(
                    range=[margen, resumen['% relecturas necesarias'].max() * 1.05]
                ),
                template='plotly_white'
            )

            st.plotly_chart(fig, use_container_width=True)

        if tipo == '% de Estimados ✍🏻':
            df['estimado'] = df['estimado'].astype(bool)

            resumen = df.groupby('periodo').agg(
                total_registros=('estimado', 'count'),
                estimados=('estimado', 'sum')
            ).reset_index()

            resumen['% de estimados'] = round(
                resumen['estimados'] * 100 / resumen['total_registros'], 2
            )

            min_valor = resumen['% de estimados'].min()
            margen = min_valor * 0.9

            fig = px.line(
                resumen,
                x='periodo',
                y='% de estimados',
                markers=True,
                title='% de Estimados ✍🏻'
            )

            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=resumen['periodo'].tolist()[:3]
                ),
                yaxis=dict(
                    range=[margen, resumen['% de estimados'].max() * 1.05]
                ),
                template='plotly_white'
            )

            st.plotly_chart(fig, use_container_width=True)

        if tipo == '% de Acumulados 📭':
            df['acumulado'] = df['acumulado'].astype(bool)

            resumen = df.groupby('periodo').agg(
                total_registros=('acumulado', 'count'),
                acumulados=('acumulado', 'sum')
            ).reset_index()

            resumen['% de acumulados'] = round(
                resumen['acumulados'] * 100 / resumen['total_registros'], 2
            )

            min_valor = resumen['% de acumulados'].min()
            margen = min_valor * 0.9

            fig = px.line(
                resumen,
                x='periodo',
                y='% de acumulados',
                markers=True,
                title='% de Acumulados 📭'
            )

            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=resumen['periodo'].tolist()[:3]
                ),
                yaxis=dict(
                    range=[margen, resumen['% de acumulados'].max() * 1.05]
                ),
                template='plotly_white'
            )

            st.plotly_chart(fig, use_container_width=True)

        if tipo == 'Total kW a refacturar 🔄':
            df_filtrado = df[df['kwRefacturar'] > 0]

            resumen = df_filtrado.groupby('periodo').agg(
                total_kw_refacturar=('kwRefacturar', 'sum')
            ).reset_index()

            resumen['total_kw_refacturar'] = resumen['total_kw_refacturar'].round(2)

            min_valor = resumen['total_kw_refacturar'].min()
            margen = min_valor * 0.9 if min_valor > 0 else 0

            fig = px.line(
                resumen,
                x='periodo',
                y='total_kw_refacturar',
                markers=True,
                title='Total kW a refacturar 🔄'
            )

            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=resumen['periodo'].tolist()[:3]
                ),
                yaxis=dict(
                    title='kW',
                    range=[margen, resumen['total_kw_refacturar'].max() * 1.05]
                ),
                template='plotly_white'
            )

            st.plotly_chart(fig, use_container_width=True)

        if tipo == 'Lecturas inconsistentes 🧐':
            df['inconsistente'] = df['observacionFacturacion'].notna() & (
                df['observacionFacturacion'].str.strip() != ''
            )

            resumen = df.groupby('periodo').agg(
                total_registros=('inconsistente', 'count'),
                inconsistentes=('inconsistente', 'sum')
            ).reset_index()

            resumen['% lecturas inconsistentes'] = round(
                resumen['inconsistentes'] * 100 / resumen['total_registros'], 2
            )

            min_valor = resumen['% lecturas inconsistentes'].min()
            margen = min_valor * 0.9

            fig = px.line(
                resumen,
                x='periodo',
                y='% lecturas inconsistentes',
                markers=True,
                title='Lecturas inconsistentes 🧐'
            )

            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=resumen['periodo'].tolist()[:3]
                ),
                yaxis=dict(
                    range=[margen, resumen['% lecturas inconsistentes'].max() * 1.05]
                ),
                template='plotly_white'
            )

            st.plotly_chart(fig, use_container_width=True)

        if tipo == '% Lectura en ubicación inexacta 📌':
            df['ubicacion_inexacta'] = df['banderaAmarilla'] | df['banderaRoja']

            resumen = df.groupby('periodo').agg(
                total_registros=('ubicacion_inexacta', 'count'),
                inexactas=('ubicacion_inexacta', 'sum')
            ).reset_index()

            resumen['% ubicación inexacta'] = round(
                resumen['inexactas'] * 100 / resumen['total_registros'], 2
            )

            min_valor = resumen['% ubicación inexacta'].min()
            margen = min_valor * 0.9

            fig = px.line(
                resumen,
                x='periodo',
                y='% ubicación inexacta',
                markers=True,
                title='% Lectura en ubicación inexacta 📌'
            )

            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=resumen['periodo'].tolist()[:3]
                ),
                yaxis=dict(
                    range=[margen, resumen['% ubicación inexacta'].max() * 1.05]
                ),
                template='plotly_white'
            )

            st.plotly_chart(fig, use_container_width=True)

        if tipo == 'Observaciones 👀':
            df['con_observacion'] = df['observacionLectura'].notna() & (
                df['observacionLectura'].str.strip() != ''
            )

            resumen = df.groupby('periodo').agg(
                total_registros=('con_observacion', 'count'),
                observadas=('con_observacion', 'sum')
            ).reset_index()

            resumen['% con observación'] = round(
                resumen['observadas'] * 100 / resumen['total_registros'], 2
            )

            min_valor = resumen['% con observación'].min()
            margen = min_valor * 0.9

            fig = px.line(
                resumen,
                x='periodo',
                y='% con observación',
                markers=True,
                title='Observaciones 👀'
            )

            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=resumen['periodo'].tolist()[:3]
                ),
                yaxis=dict(
                    range=[margen, resumen['% con observación'].max() * 1.05]
                ),
                template='plotly_white'
            )

            st.plotly_chart(fig, use_container_width=True)
