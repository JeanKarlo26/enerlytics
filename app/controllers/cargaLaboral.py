import pandas as pd
import streamlit as st
import numpy as np
from controllers.conection import MongoDBConnection

class CargaLaboral:
    def __init__(self):
        self.conexion = MongoDBConnection()
        self.collectionSigof = self.conexion.get_collection('tblSigof')
        self.collectionFU = self.conexion.get_collection('tblFichaUnica')
        self.collectionLast = self.conexion.get_collection('tblLastPeriodo')
        self.collectionLimiteRuta = self.conexion.get_collection('tblLimiteRuta')

        self.dfRectangulo = pd.DataFrame(list(self.collectionLimiteRuta.find({'estado': 1})))


    def calcular_tiempo_sin_comida(self, row):
        inicio = row['inicio']
        fin = row['fin']
        
        # Convertir a datetime para calcular diferencias
        inicio_dt = pd.Timestamp(inicio)
        fin_dt = pd.Timestamp(fin)
        
        # Duración total del trabajo en minutos
        duracion_total = (fin_dt - inicio_dt).total_seconds() / 60
        
        # Restar 90 minutos para almuerzo si el trabajo abarca el periodo de 12:00 - 15:00
        if inicio_dt <= pd.Timestamp(inicio_dt.date()).replace(hour=12, minute=0) and fin_dt >= pd.Timestamp(inicio_dt.date()).replace(hour=15, minute=0):
            duracion_total -= 90
        
        # Restar 30 minutos para el desayuno si el trabajo abarca el periodo de 7:00 - 8:00
        if inicio_dt <= pd.Timestamp(inicio_dt.date()).replace(hour=7, minute=0) and fin_dt >= pd.Timestamp(inicio_dt.date()).replace(hour=8, minute=0):
            duracion_total -= 30
        
        return duracion_total
    
    def punto_fuera_ruta(self, row):
        #Obtenemos La ruta y el limite de la ruta 
        ruta = row['ruta_nuevo']
        rect = self.dfRectangulo[self.dfRectangulo['ruta'] == ruta]
        
        if not rect.empty:
            #definimos los puntos del rectangulo
            min_lat = rect['min_lat'].values[0]
            max_lat = rect['max_lat'].values[0]
            min_lon = rect['min_lon'].values[0]
            max_lon = rect['max_lon'].values[0]
            #y evaluamos si el punto esta dentro o fuera del cuadro
            if (row['latitud'] < min_lat) or (row['latitud'] > max_lat) or (row['longitud'] < min_lon) or (row['longitud'] > max_lon):
                return True
        return False
    
    def calcular_reduccion(self, grupo):
        #En principo ninguna ruta tiene reduccion ( en base al lecturista y a la fecha)
        grupo['reduccionalmuerzo'] = False
        grupo['tiempo_de_reduccion'] = 0

        grupo['fecha_ejecucion'] = pd.to_datetime(grupo['fecha_ejecucion'])        

        #establecemos un margen de las 12 a las 15, es decir 3 horas 
        lower_bound = pd.to_datetime(grupo['fecha_ejecucion'].dt.date) + pd.Timedelta(hours=12)
        upper_bound = pd.to_datetime(grupo['fecha_ejecucion'].dt.date) + pd.Timedelta(hours=15)
        
        #aquellos anomalos ( si es diferente al resto), que no se identifique fuera del limite de coordenadas
        #que el tiempo de trabajo sea mayor igual a 20 (seria tiempo de comer mas de 20 min) 
        # y los que tienen fecha de ejecucion en el margen de las 3 horas
        condicion = (
            (grupo['bandera_azul'] == True) &
            (grupo['bandera_roja'] == False) &
            (grupo['tiempo_trabajado'] >= 20) &
            (grupo['fecha_ejecucion'] >= lower_bound) &
            (grupo['fecha_ejecucion'] <= upper_bound)
        )
        
        filas_validas = grupo[condicion]

        #Solo se valida una fila porque es improbable que haya almorzado dos veces, y no se podria garantizar la confiabilidad
        if len(filas_validas) == 1:
            idx = filas_validas.index[0]
            grupo.loc[idx, 'reduccionalmuerzo'] = True
            # se reduce el todo el tiempo trabajado de esa fila
            grupo.loc[idx, 'tiempo_de_reduccion'] = grupo.loc[idx, 'tiempo_trabajado']
        return grupo

    def evaluarCarga(self, df):
        #convertimos el tipo de la columan de ejecucion
        df['fecha_ejecucion'] = pd.to_datetime(df['fecha_ejecucion'])

        # Ordenar por lecturista, ruta, fecha_ejecucion
        df = df.sort_values(by=['lecturista', 'ruta_nuevo', 'fecha_ejecucion'])

        # Reemplazar fechas en blanco con la última fecha válida por ruta
        df['fecha_ejecucion'] = df.groupby(['lecturista', 'ruta_nuevo'])['fecha_ejecucion'].ffill()

        # Volver a ordenar por lecturista, fecha_ejecucion, ruta_nuevo
        df = df.sort_values(by=['lecturista', 'fecha_ejecucion', 'ruta_nuevo'])

        # Crear una columna para agrupar rutas interrumpidas (rutas que se hicieron de corrido)
        df['grupo_ruta'] = (df['ruta_nuevo'] != df['ruta_nuevo'].shift()).cumsum()

        # Calcular el tiempo trabajado por día (en minutos)
        df['tiempo_trabajado'] = df.groupby(['lecturista', 'fecha'])['fecha_ejecucion'].diff().fillna(pd.Timedelta(seconds=0)).dt.total_seconds() / 60

        #Calfular aquellos que se encuentran fuera de ruta
        df['fuera_ruta'] = df.apply(self.punto_fuera_ruta, axis=1)

        dfResumen = df.groupby(['lecturista', 'fecha'], group_keys=False).apply(self.calcular_reduccion)

        resumen_diario = dfResumen.groupby(['lecturista', 'fecha']).agg({
            'suministro': 'count',
            'fecha_ejecucion': ['min', 'max'],
            'tiempo_trabajado': 'sum',
            'reduccionalmuerzo': 'any',
            'tiempo_de_reduccion': 'sum'
        }).reset_index()

        resumen_diario.columns = ['lecturista', 'fecha', 'suministro', 'inicio', 'fin', 'tiempo_trabajado', 'reduccionalmuerzo', 'tiempo_de_reduccion']

        resumen_diario['tiempo_neto'] = resumen_diario['tiempo_trabajado'] - resumen_diario['tiempo_de_reduccion']
        resumen_diario.loc[~resumen_diario['reduccionalmuerzo'], 'tiempo_neto'] = resumen_diario['tiempo_trabajado']

        resumen_diario['carga'] = resumen_diario['tiempo_neto'] > 480

        # Agrupar y contar cantidad de suministros
        grouped = df.groupby(['lecturista', 'grupo_ruta', 'ruta_nuevo']).agg({
            'fecha_ejecucion': ['min', 'max']
        }).reset_index()

        # Renombrar columnas
        grouped.columns = ['lecturista', 'grupo', 'ruta', 'inicio', 'fin']

        # Identificar registros que abarcan más de un día
        grouped['diferente'] = grouped['inicio'].dt.date != grouped['fin'].dt.date

        # Crear nuevas filas para registros que abarcan más de un día
        day_part = grouped[grouped['diferente']].copy()
        day_part['fin'] = day_part['inicio'].apply(lambda dt: dt.replace(hour=23, minute=59, second=59))

        night_part = grouped[grouped['diferente']].copy()
        night_part['inicio'] = night_part['fin'].apply(lambda dt: dt.replace(hour=0, minute=0, second=0))

        # Concatenar las partes diurnas y nocturnas con el resto de los datos
        grouped = pd.concat([grouped[~grouped['diferente']], day_part, night_part])

        # Calcular el tiempo de ejecución en minutos
        grouped['tiempo_lectura'] = (grouped['fin'] - grouped['inicio']).dt.total_seconds() / 60

        # Revisar si hay valores NA o infinitos en la columna 'tiempo_lectura'
        grouped['tiempo_lectura'] = grouped['tiempo_lectura'].replace([np.inf, -np.inf], np.nan).fillna(0)

        grouped['apariciones_mismo_lecturador'] = grouped.groupby(['lecturista', 'ruta'])['ruta'].transform('count')

        # Contar el número de lecturistas únicos que han registrado la misma ruta
        lecturistas_unicos = df.groupby('ruta_nuevo')['lecturista'].nunique().reset_index()
        lecturistas_unicos.columns = ['ruta', 'apariciones_todos_lecturadores']

        # Unir la información de lecturistas únicos con el DataFrame agrupado
        grouped = grouped.merge(lecturistas_unicos, on='ruta', how='left')

        return df, grouped, resumen_diario