import pandas as pd
import numpy as np
import streamlit as st
from controllers.conection import MongoDBConnection
from controllers.periodo import Pfactura
from pymongo.errors import PyMongoError

class FichaUnica:
    def __init__(self):
        self.conexion = MongoDBConnection()
        self.Pfactura = Pfactura()
        self.lastPeriodo = self.Pfactura.getLastPeriodo()
        self.collectionFU = self.conexion.get_collection('tblFichaUnica')
        self.collectionFotoLectura = self.conexion.get_collection('tblFotoLectura')

    def resta_abs(self, group):
        umbral = 0.00011
        resta = abs(group.max() - group.min()) 
        return 1 if umbral >= resta else resta

    def crear_nuevo_dataset(self, df_registros):
        if not df_registros.empty:
            self.lastPeriodo = self.Pfactura.getLastPeriodo()
            df_agrupado = df_registros.groupby(['suministro', 'ciclo', 'sector', 'ruta']).agg({
                'latitud': 'median',
                'longitud': 'median',
                'id': 'count',
                'pfactura': ['first', 'last']
            }).reset_index()

            df_agrupado.columns = ['suministro', 'ciclo', 'sector', 'ruta', 'latitud', 'longitud', 'cantidad', 'periodo_inicio', 'periodo_fin']
            
            df_agrupado['estado'] = df_agrupado['periodo_fin'].apply(lambda x: 1 if x == self.lastPeriodo else 0)
            df_agrupado['periodo_fin'] = df_agrupado['periodo_fin'].apply(lambda x: None if x == self.lastPeriodo else x)

            return df_agrupado
        return pd.DataFrame()
    
    def calculoHaversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Radio de la Tierra en kilómetros
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        return R * c * 1000
    
    def guardarNuevos(self, df):
        df_nuevo_dataset = self.crear_nuevo_dataset(df)
        self.conexion.guardar_en_mongo(df_nuevo_dataset, self.collectionFU)
        return df_nuevo_dataset
    
    def getNuevos(self, df):
        newDF = df[['suministro', 'ciclo', 'sector', 'ruta', 'latitud','longitud','suministro','pfactura']].copy()
        newDF.columns = ['suministro','ciclo','sector','ruta','latitud','longitud','cantidad','periodo_inicio']
        newDF['periodo_fin'] = None
        newDF['cantidad'] = 1
        newDF['estado'] = 1
        return newDF
    
    def updateRetirado(self, df, collection, session=None):
        if not df.empty:
            query = df.to_dict('records')
            new_values = {"$set": {
                "estado": 0,
                "periodo_fin": self.Pfactura.getSecondLastPeriodo()
            }}
            collection.update_many({"$or": query}, new_values, session=session)

    def updateReincorporados(self, lista, df):
        # BUSCA el último documento por suministro, asegurando que obtengas solo el más reciente basado en periodo_fin.
        pipeline = [
            {"$match": {"suministro": {"$in": lista}}},
            {"$sort": {"suministro": 1, "periodo_fin": -1}},
            {"$group": {
                "_id": "$suministro",
                "suministro": {"$first": "$suministro"},
                "periodo_fin": {"$first": "$periodo_fin"},
                "documento_completo": {"$first": "$$ROOT"}
            }},
            {"$replaceRoot": {"newRoot": "$documento_completo"}},
            {"$project": { "_id": 0 }}
        ]

        dfFU = pd.DataFrame(list(self.collectionFU.aggregate(pipeline)))

        # SE UNEN AMBOS DF, Y LOS CAMPOS QUE SE REPITEN TIENEN UN NUEVO SUFIJO
        df_completo = pd.merge(df, dfFU, on='suministro', suffixes=('_nuevo', '_original'), how='outer', indicator=True)
        
        # SE EVALUA SI CAMBIO LA RUTA EN LA QUE SE ENCONTRABAN
        df_completo['cambio'] = (
            (df_completo['ciclo_nuevo'] != df_completo['ciclo_original']) |
            (df_completo['sector_nuevo'] != df_completo['sector_original']) |
            (df_completo['ruta_nuevo'] != df_completo['ruta_original'])
        )

        # DISTANCIA ENTRE LOS DOS PUNTOS (EL ANTERIOR Y EL ACTUAL)
        df_completo['distancia_metros'] = df_completo.apply(lambda row: 
            self.calculoHaversine(row['latitud_nuevo'], row['longitud_nuevo'], row['latitud_original'], row['longitud_original']), 
            axis=1
        )

        # SE IGNORAN LOS QUE TIENEN UNA DIFERENCIA DE 20 METROS, 
        # UN WARNING SI ESTA ENTRE 20 Y 100, Y NO HAYAN CAMBIADO DE UBICACION,
        # Y DANGER SI ESTA A MAS DE 100 Y NO CAMBIO, O NO SE REGISTRA LA DISTANCIA
        df_completo['bandera_amarilla'] = (df_completo['distancia_metros'] < 100) & (df_completo['distancia_metros'] > 20) & (~df_completo['cambio'])
        df_completo['bandera_roja'] = ((df_completo['distancia_metros'] >= 100) & (~df_completo['cambio'])) | (df_completo['distancia_metros'].isnull())

        #SE OBTIENE TODOS LOS SUMINISTROS QUE CAMBIARON DE UBICACION 
        suministros = df_completo[df_completo['cambio']]['suministro'].tolist()

        columnas_final = ['suministro','ciclo','sector','ruta','latitud','longitud','cantidad','periodo_inicio','periodo_fin','estado']
        columnas_nuevo = ['suministro','ciclo_nuevo','sector_nuevo','ruta_nuevo','latitud_nuevo','longitud_nuevo','cantidad_nuevo','periodo_inicio_nuevo','periodo_fin_original','estado']
        columnas_continua = ['suministro','ciclo_nuevo','sector_nuevo','ruta_nuevo','latitud_original','longitud_original','cantidad_nuevo','periodo_inicio_nuevo','periodo_fin_original','estado']
       
        dfFU1 = df_completo[df_completo['suministro'].isin(suministros)][columnas_nuevo]
        dfFU2 = df_completo[~df_completo['suministro'].isin(suministros)][columnas_continua]

        dfFU1.columns = columnas_final
        dfFU2.columns = columnas_final
        dfFUCompleto = pd.concat([dfFU1,dfFU2], ignore_index=True)

        dfFUCompleto['estado'] = 1
        dfFUCompleto['periodo_fin'] = None
        
        return df_completo[['suministro', 'ciclo_nuevo','sector_nuevo','ruta_nuevo','distancia_metros','bandera_amarilla','bandera_roja']], dfFUCompleto

    def updateCambiados(self, df):
        if not df.empty:
            # SE OBTIENE LA LISTA DE LOS CAMBIADOS Y SE ESTABLECE EN ESTADO CERO LOS VALORES ANTERIORES
            listaSuministros = df['suministro'].unique().tolist()

            #SE OBTIENE LOS WARNING Y DANGER DE DISTANCIA
            df['bandera_amarilla'] = (df['distancia_metros'] < 100) & (df['distancia_metros'] > 20)
            df['bandera_roja'] = (df['distancia_metros'] >= 100) | (df['distancia_metros'].isnull())

            #SE OBTIENE LAS RUTAS UNICAS QUE ENTREN EN EL UMBRAL DE DISTANCIA
            rutas_solo_nombre = df[df['distancia_metros'] < 20]['ruta_nuevo'].unique().tolist()

            #PARA LAS RUTAS QUE NO ENTRAN EN EL UMBRAL SE TOMA LA LATITUD ANTERIOR PERO TIENEN QUE ENTRAR EN UN PROCESO DE EVALUACION
            columnas_final = ['suministro','ciclo','sector','ruta','latitud','longitud','cantidad','periodo_inicio','periodo_fin','estado']
            columnas_nuevo = ['suministro','ciclo_nuevo','sector_nuevo','ruta_nuevo','latitud_nuevo','longitud_nuevo','cantidad_nuevo','periodo_inicio_nuevo','periodo_fin_original','estado']
            columnas_continua = ['suministro','ciclo_nuevo','sector_nuevo','ruta_nuevo','latitud_original','longitud_original','cantidad_nuevo','periodo_inicio_nuevo','periodo_fin_original','estado']
            dfFU1 = df[df['ruta_nuevo'].isin(rutas_solo_nombre)][columnas_continua]
            dfFU2 = df[~df['ruta_nuevo'].isin(rutas_solo_nombre)][columnas_nuevo]

            dfFU1.columns = columnas_final
            dfFU2.columns = columnas_final

            dfFU = pd.concat([dfFU1,dfFU2], ignore_index=True)

            return df[['suministro', 'ciclo_nuevo','sector_nuevo','ruta_nuevo','distancia_metros','bandera_amarilla','bandera_roja']], dfFU, listaSuministros

    def updateNormal(self, df):
        if not df.empty:
            df['bandera_amarilla'] = (df['distancia_metros'] < 100) & (df['distancia_metros'] > 20)
            df['bandera_roja'] = (df['distancia_metros'] >= 100) | (df['distancia_metros'].isnull())

            listaSuministros = df['suministro'].unique().tolist()

            return df[['suministro', 'ciclo_nuevo','sector_nuevo','ruta_nuevo','distancia_metros','bandera_amarilla','bandera_roja']], listaSuministros

    def frecuenciaFotografica(self, df, collection, session=None):
        suministros = df[df['foto'] == 'ver foto']['suministro'].tolist()
        # suministrosSinFotoF = df[~df['suministro'].isin(suministrosConFotosF)]['suministro'].tolist()
        
        #EL INDICADOR ES LA CANTIDAD DE MESES SIN FOTO

        #TODOS LOS QUE TIENEN FOTO SE COLOCA EL INDICADOR EN 0
        collection.update_many(
            {"suministro": {"$in": suministros}, "estado": 1},
            {"$set": {"indicador_foto": 0}},
            session=session
        )
        #SINO NO TIENE FOTO TIENE QUE SUMARSE 1
        collection.update_many(
            {"suministro": {"$nin": suministros}, "estado": 1},
            {"$inc": {"indicador_foto": 1}},
            session=session
        )

    def suministroSinLectura(self, df, collection, session=None):
        suministros = df[df['lectura'].isna() | (df['lectura'] == '')]['suministro'].tolist()
        #EL INDICADOR ES LA CANTIDAD DE MESES SIN LECTURA

        collection.update_many(
            {"suministro": {"$in": suministros}, "estado": 1},
            {"$inc": {"sin_lectura": 1}},
            session=session
        )

        collection.update_many(
            {"suministro": {"$nin": suministros}, "estado": 1},
            {"$set": {"sin_lectura": 0}},
            session=session
        )

    def updateFotoLecturaMensual(self, periodo):
        df = pd.DataFrame(list(self.collectionFU.find(
            { "estado": 1 },
            { "_id": 0, "suministro": 1, 'ciclo':1, 'sector':1, 'ruta':1, "indicador_foto": 1, "sin_lectura": 1 }
        )))

        df['periodo'] = periodo

        self.conexion.guardar_en_mongo(df, self.collectionFotoLectura, session=None)

