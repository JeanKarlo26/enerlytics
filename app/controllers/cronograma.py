import pandas as pd
import numpy as np
import streamlit as st
from controllers.conection import MongoDBConnection
from datetime import datetime, timedelta

class Cronograma:
    def __init__(self):
        self.conexion = MongoDBConnection()
        self.ciclos_diccionario = {
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
        self.short_name = {
            '6149 - Ciclo 08 Huánuco': 'Ciclo 08',
            '6698 - Ciclo 13.08 Huánuco': 'Ciclo 13.08',
            '6705 - Ciclo 14.08 Huánuco': 'Ciclo 14.08',
            '6713 - Ciclo 15.08 Huánuco': 'Ciclo 15.08',
            '6150 - Ciclo 09 Huánuco': 'Ciclo 09',
            '6699 - Ciclo 13.09 Huánuco': 'Ciclo 13.09',
            '6706 - Ciclo 14.09 Huánuco': 'Ciclo 14.09',
            '6714 - Ciclo 15.09 Huánuco': 'Ciclo 15.09',
            '6151 - Ciclo 10 Huánuco': 'Ciclo 10',
            '6692 - Ciclo 11.10 Huánuco': 'Ciclo 11.10',
            '6695 - Ciclo 12.10 Huánuco': 'Ciclo 12.10',
            '6700 - Ciclo 13.10 Huánuco': 'Ciclo 13.10',
            '6707 - Ciclo 14.10 Huánuco': 'Ciclo 14.10',
            '6715 - Ciclo 15.10 Huánuco': 'Ciclo 15.10',
            '6153 - Ciclo 11 Huánuco': 'Ciclo 11',
            '6696 - Ciclo 12.11 Huánuco': 'Ciclo 12.11',
            '6701 - Ciclo 13.11 Huánuco': 'Ciclo 13.11',
            '6708 - Ciclo 14.11 Huánuco': 'Ciclo 14.11',
            '6716 - Ciclo 15.11 Huánuco': 'Ciclo 15.11',
            '6157 - Ciclo 12 Huánuco': 'Ciclo 12',
            '6702 - Ciclo 13.12 Huánuco': 'Ciclo 13.12',
            '6709 - Ciclo 14.12 Huánuco': 'Ciclo 14.12',
            '6717 - Ciclo 15.12 Huánuco': 'Ciclo 15.12',
            '6162 - Ciclo 13 Huánuco': 'Ciclo 13',
            '6710 - Ciclo 14.13 Huánuco': 'Ciclo 14.13',
            '6718 - Ciclo 15.13 Huánuco': 'Ciclo 15.13',
            '6163 - Ciclo 14 Huánuco': 'Ciclo 14',
            '6719 - Ciclo 15.14 Huánuco': 'Ciclo 15.14',
            '6169 - Ciclo 15 Huánuco': 'Ciclo 15'
        }
        self.collectionSigof = self.conexion.get_collection('tblSigof')
        # self.collectionFU = self.conexion.get_collection('tblFichaUnica')
        # self.collectionLast = self.conexion.get_collection('tblLastPeriodo')
    
    # Función para calcular límites de IQR
    def calcular_limites_iqr(self, grupo):
        Q1 = grupo.quantile(0.25)
        Q3 = grupo.quantile(0.75)
        IQR = Q3 - Q1
        limite_superior = Q3 + 1.5 * IQR
        return (grupo > limite_superior) and (grupo > timedelta(minutes=2))
    
    # Función para calcular límites de IQR y marcar anomalías
    def marcar_ultimos(self, grupo):
        total = len(grupo)
        ultimos_porcentaje = int(np.ceil(total * 0.15))
        grupo['bandera_azul'] = False
        ultimos = grupo.tail(ultimos_porcentaje).copy()
        
        Q1 = grupo['tiempo_ejecucion'].quantile(0.25)
        Q3 = grupo['tiempo_ejecucion'].quantile(0.75)
        IQR = Q3 - Q1
        limite_superior = Q3 + 1.5 * IQR
        grupo['limite'] = limite_superior
        ultimos['bandera_azul'] = ((ultimos['tiempo_ejecucion'] > limite_superior) & \
                                    (ultimos['tiempo_ejecucion'] > timedelta(minutes=2)))
                                    # (~ultimos['cronograma'])
        grupo.update(ultimos)
        
        return grupo
    
    # Función para verificar el suministro cerrado en cada grupo
    def verificar_suministro_grupo(self, grupo):
        grupo.reset_index(inplace=True)
        bandera_azul_idx = grupo[grupo['bandera_azul']].index
        
        if not bandera_azul_idx.empty:
            bandera_azul_idx = bandera_azul_idx[0]
            num_filas = len(grupo)

            if num_filas <= 30:
                ultimos_n = 5
            elif num_filas > 30 and num_filas <= 100:
                ultimos_n = 10
            else:
                ultimos_n = 20

            # Verificar si la bandera azul está en los últimos n filas
            if bandera_azul_idx >= len(grupo) - ultimos_n:
                grupoTemp = grupo.loc[bandera_azul_idx:]
            else:
                grupoTemp = grupo.iloc[-ultimos_n:]
            
            for idx, row in grupoTemp.iterrows():
                if row['bandera_roja'] | row['bandera_amarilla']:

                    grupo.loc[idx, 'suministro_cerrado'] = True
                elif row['relectura']:
                    grupo.loc[idx, 'suministro_cerrado'] = False
                else:
                    grupo.loc[idx, 'suministro_cerrado'] = row['tiempo_ejecucion'].total_seconds() > 7200
                    
        return grupo
    
    # Consideración de días consecutivos
    def es_diferente_dia(self, fila):
        if fila['diferente_dia']:
            # Si la diferencia de tiempo no es significativa (por ejemplo, menos de 2 horas), no se marca como anómalo
            if abs((fila['fecha_ejecucion'] - pd.to_datetime(fila['dia_ejecucion_major'])).total_seconds()) <= 7200:
                return False
            return True
        return False
    
    def marcar_suministros(self, grupo):
        grupo['bandera_verde'] = False

        # Verificar si todas las ejecuciones están en un solo día o dos días consecutivos
        fechas = grupo['fecha'].dropna().unique()

        if len(fechas) == 0:
            grupo['bandera_verde'] = True
            return grupo
        
        if len(fechas) == 1:
            return grupo
        
        #Buscamos si hay dia segun cronograma correcto
        dia_cronograma = grupo.loc[grupo['cronograma'], 'fecha'].mode()
        if not dia_cronograma.empty:
            dia_cronograma = dia_cronograma.iloc[0]
        #Sino la moda de la Fecha
        else:
            dia_cronograma = grupo['fecha'].mode().iloc[0]

        if len(fechas) == 2:
            fecha_min, fecha_max = min(fechas), max(fechas)
            #si hay un solo dia de diferencia
            if (fecha_max - fecha_min).days == 1:
                ejecuciones_dia_min = grupo[grupo['fecha'] == fecha_min]['fecha_ejecucion']
                ejecuciones_dia_max = grupo[grupo['fecha'] == fecha_max]['fecha_ejecucion']
                #Si la fecha mayor es la del cronograma se tiene que comprobar todas las que tienen fecha minima
                if fecha_max == dia_cronograma:

                    ejecucion_max = ejecuciones_dia_max.min()
                    for ejecucion_min in ejecuciones_dia_min:
                        diferencia = abs((ejecucion_max - ejecucion_min).total_seconds())
                        if diferencia > 3600: 
                            grupo.loc[grupo['fecha_ejecucion'] == ejecucion_min, 'bandera_verde'] = True

                #Si la fecha minima es la del cronograma se tiene que comprobar todas las que tienen fecha maxima
                if fecha_min == dia_cronograma:

                    ejecucion_min = ejecuciones_dia_min.max()
                    for ejecucion_max in ejecuciones_dia_max:
                        diferencia = abs((ejecucion_max - ejecucion_min).total_seconds())
                        if diferencia > 3600: 
                            grupo.loc[grupo['fecha_ejecucion'] == ejecucion_max, 'bandera_verde'] = True

                return grupo
     
        # Marcar los suministros que no coinciden con el día de cronograma o mayoritario
        grupo['bandera_verde'] = grupo['fecha'] != dia_cronograma

        return grupo
    
    def getDiaCorrecto(self, row):
        ciclo = row['ciclo']
        pfactura = row['pfactura']
        
        pfactura_str = str(pfactura)
        anio = int(pfactura_str[:4])
        mes = int(pfactura_str[4:])
        if mes == 12:
            ultimo_dia_mes = 31
        else:
            ultimo_dia_mes = (datetime(anio, mes+1, 1) - timedelta(days=1)).day
        
        # Calcular el día correcto de ejecución según el diccionario
        dias_resto = self.ciclos_diccionario[ciclo]

        return ultimo_dia_mes - dias_resto

    def verificar_ejecucion(self, row):
        ciclo = row['ciclo']
        pfactura = row['pfactura']
        fecha_ejecucion = row['fecha_ejecucion']
        
        # Si no hay fecha de ejecución, marcar como False
        if pd.isna(fecha_ejecucion):
            return False
        
        pfactura_str = str(pfactura)
        anio = int(pfactura_str[:4])
        mes = int(pfactura_str[4:])
        if mes == 12:
            ultimo_dia_mes = 31
        else:
            ultimo_dia_mes = (datetime(anio, mes+1, 1) - timedelta(days=1)).day
        
        # Calcular el día correcto de ejecución según el diccionario
        dias_resto = self.ciclos_diccionario[ciclo]

        dia_correcto = ultimo_dia_mes - dias_resto
        
        # Verificar si la ejecución es correcta
        #puede ser 20 min antes o 20 minutos despues
        margen = timedelta(minutes=20)
        
        fecha_correcta_inicio = datetime(anio, mes, dia_correcto)
        fecha_correcta_fin = fecha_correcta_inicio.replace(hour=23, minute=59, second=59)
        
        if fecha_correcta_inicio - margen <= fecha_ejecucion <= fecha_correcta_fin + margen:
            return True
        else:
            return False
        
    def tiempo_ejecucion(self, df):
        #ordenamos el Frame
        df = df.sort_values(by=['ciclo_nuevo','sector_nuevo','ruta_nuevo','fecha_ejecucion'])
        
        df['fecha'] = df['fecha_ejecucion'].dt.date
        df = df.groupby('ruta_nuevo', group_keys=False).apply(self.marcar_suministros)

        # Calcular el tiempo de ejecución dentro de cada ruta entre cada suministro
        df['tiempo_ejecucion'] = df.groupby('ruta_nuevo')['fecha_ejecucion'].diff().fillna(pd.Timedelta(seconds=0))
        
        # Aplicar la conversión a la columna 'tiempo_ejecucion'
        df = df.groupby('ruta_nuevo', group_keys=False).apply(self.marcar_ultimos)

        #Sumamos todo el tiempo de los suministros
        dfTiempoRuta = df.groupby('ruta_nuevo')['tiempo_ejecucion'].sum().reset_index()

        # Renombrar columna para evitar colisiones durante el merge
        dfTiempoRuta = dfTiempoRuta.rename(columns={'tiempo_ejecucion': 'tiempo_ejecucion_ruta'})

        # Fusionar con df
        df = df.merge(dfTiempoRuta, on='ruta_nuevo', how='left')

        return df



        
