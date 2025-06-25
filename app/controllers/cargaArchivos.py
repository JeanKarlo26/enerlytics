import pandas as pd
from controllers.conection import MongoDBConnection
from controllers.coordenadas import Coordenadas
from controllers.fichaUnica import FichaUnica
from controllers.cronograma import Cronograma
from controllers.cargaLaboral import CargaLaboral
from controllers.periodo import Pfactura

from pymongo import MongoClient
from pymongo.errors import PyMongoError, InvalidOperation

import re
import numpy as np
import streamlit as st
import hashlib
import time

class CleanData:
    def __init__(self):
        pass
        
    def cleanRuta(self, text):
        # Reemplazar caracteres especiales por tildes
        replacements = {
            'á': r'a´', 'é': r'e´', 'í': r'i´', 'ó': r'o´', 'ú': r'u´', 'é': 'Ã©',
            'Á': r'A´', 'É': r'E´', 'Í': r'I´', 'Ó': r'O´', 'Ú': r'U´'
        }
        for k, v in replacements.items():
            text = re.sub(v, k, text)

        #Convertir a mayusculas
        text = text.upper()
        
        # Eliminar puntos de abreviaciones
        text = re.sub(r'\.', '', text)

        # Eliminar guiones sin espacio
        text = re.sub(r'-', ' - ', text)
        
        # Eliminar dobles espacios
        text = re.sub(r'\s{2,}', ' ', text)

        # Eliminar espacios en blanco en general
        text = re.sub(r'\s+', ' ', text)

        # Eliminar guiones al final de la cadena
        text = re.sub(r'-\s*$', '', text)

        #LIMPIAR CASERIOS
        text = re.sub(r'\bCAS\b', ' CASERIO ', text)

        #LIMPIAR BLOQUES
        text = re.sub(r'\bBQ\b', ' BLOQUE ', text)

        #LIMPIAR CENTRO POBLADO
        text = re.sub(r'\bCP\b', ' CENTRO POBLADO ', text)

        #LIMPIAR CENTRO POBLADO MAYOR
        text = re.sub(r'\bCPMA\b', ' CENTRO POBLADO MAYOR ', text)

        #LIMPIAR CENTRO POBLADO MENOR
        text = re.sub(r'\bCPMEN\b', ' CENTRO POBLADO MENOR ', text)
        text = re.sub(r'\bCPME\b', ' CENTRO POBLADO MENOR ', text)

        #LIMPIAR CENTRO POBLADO MAYOR
        text = re.sub(r'\bCPM\b', ' CENTRO POBLADO MAYOR ', text)

        #LIMPIAR CARRETERA
        text = re.sub(r'\bCARR\b', ' CARRETERA ', text)

        #LIMPIAR URBANIZACION
        text = re.sub(r'\bURB\b', ' URBANIZACION ', text)

        #LIMPIAR BARRIO
        text = re.sub(r'\bBARR\b', ' BARRIO ', text)

        #LIMPIAR Ñ
        text = text.replace('BAÃ?OS', 'BAÑOS')
        
        return text.strip()
    
    def corregir_caracteres(self, texto):
        return texto.replace('Ã¡', 'á').replace('ÃÂ¡', 'á')
    
    # def cleanSigof(self, periodo):
    #     conexion = MongoDBConnection()
    #     collectionSigof = conexion.get_collection('tblFichaUnica')
    #     print(f"Iniciando procesamiento para el periodo: {periodo}")
    #     for doc in list(collectionSigof.find({'periodo_inicio': periodo})):
    #         ruta_limpia = self.cleanRuta(doc['ruta'])
    #         collectionSigof.update_many({'_id': doc['_id']}, {'$set': {'ruta': ruta_limpia}})

    #     print(f"TERMINO procesamiento para el periodo: {periodo}")
    # def comprobacion(self):
    #     conexion = MongoDBConnection()
    #     collectionSigof = conexion.get_collection('tblFichaUnica')
    #     list = collectionSigof.distinct('ruta')
    #     df = pd.DataFrame(list, columns=['ruta'])
    #     st.write(df)
    #     df['ruta'] = df['ruta'].apply(self.cleanRuta)
    #     st.write(df.duplicated())
    #     st.write(df)

class CargaArchivos:
    def __init__(self):
        self.cleandata = CleanData()
        self.conexion = MongoDBConnection()
        self.coordenadas = Coordenadas()
        self.pfactura = Pfactura()
        self.fichaunica = FichaUnica()
        self.cronograma = Cronograma()
        self.cargaLaboral = CargaLaboral()
        self.collectionSigof = self.conexion.get_collection('tblSigof')
        self.collectionOptimus = self.conexion.get_collection('tblOptimus')
        self.collectionFU = self.conexion.get_collection('tblFichaUnica')
        self.collectionResultadoFinal = self.conexion.get_collection('tblResultadoFinal')
        self.collectionResultadoSigof = self.conexion.get_collection('tblResultadoSigof')
        self.collectionCargaLaboral = self.conexion.get_collection('tblCargaLaboral')
        self.collectionEscaladoRuta = self.conexion.get_collection('tblEscaladoRuta')

    def getDataPeriodo(_self, periodo):
        dfSigofList = list(_self.collectionSigof.find({'pfactura': {'$in': periodo}}))
        return pd.DataFrame(dfSigofList)

    def getAllSuministros(self):
        resultados = self.collectionFU.find({}, {'suministro': 1, '_id': 0})
        suministros = [doc['suministro'] for doc in resultados]
        return np.array(suministros)
    
    def verificarArchivo(self, tipo, uploader):
        columnas_dict = {
            'Optimus NGC': {'IdNroServicio', 'NombreNroServicio', 'Direccion', 'IdEmpresa', 'IdUUNN', 'IdCiclo', 'NombreCiclo',
                            'AbreviaTarifa', 'NivelTension', 'IdSector', 'AbreviaSector', 'IdRutaLectura', 'NombreRutaLectura',
                            'NroSecuenciaLectura', 'FechaLectura', 'IdMagnitud', 'Abreviatura', 'IdOrdenTrabajo', 'LecturaOriginal',
                            'Lectura', 'FactorMedicion', 'FactorTransformacion', 'Diferencia', 'ConsumoFacturar', 'LecturaAnterior',
                            'ConsumoAnterior', 'ConsumoAntesAnterior', 'Promedio6Meses', 'IdEstado', 'SerieFabrica', 'NroMesesDeuda',
                            'ObsLectura', 'ObsFacturacion', 'Comentario'},
            
            'Sigof': {'id', 'pfactura', 'suministro', 'medidor', 'cliente', 'direccion',
                    'lecturista', 'ciclo', 'sector', 'ruta', 'tipo_lectura', 'lectura',
                    'obs', 'obs_descripcion', 'consumo', 'fecha_ejecucion', 'fecha_asignacion',
                    'orden', 'orden_ruta', 'lcorrelati', 'resultado', 'validacion', 'ot',
                    'device_imei', 'latitud', 'longitud', 'foto'},
            
            'Reclamos': set()
        }

        # Validar que el tipo de archivo exista en el diccionario
        if tipo not in columnas_dict:
            return 'tipoNoValido', pd.DataFrame()

        dfs = []  # Lista para almacenar los DataFrames
        columnas_requeridas = columnas_dict[tipo]

        # Leer y validar archivos
        for file in uploader:
            df = pd.read_excel(file, skiprows=5) if tipo == 'Optimus NGC' else pd.read_excel(file)
            
            if not columnas_requeridas.issubset(set(df.columns)):
                return 'noCoincide', pd.DataFrame()
            
            dfs.append(df)

        # Concatenar todos los archivos en un solo paso
        dfConcat = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

        return tipo, dfConcat
    
    def comprobacion(self, df):
        #obtenemos todos los periodos de nuestros archivos
        pfacturas = df['pfactura'].unique().tolist()

        #Consulta a la BD por los archivos de esos periodos
        dfSigof = self.getDataPeriodo(pfacturas)

        #si encontramos archivos en esos periodos eliminamos para trabajar con frames homogeneos
        if not dfSigof.empty:
            dfSigof.drop(columns=['_id'], inplace=True)

        dfMerge = pd.concat([dfSigof, df], ignore_index=True)

        #obtenemos todos los duplicados 
        duplicados = dfMerge[dfMerge.duplicated(subset=['suministro', 'pfactura'], keep=False)]

        #Hay mas de un registro de los duplicados, por eso eliminamos
        duplicados_unicos = duplicados.drop_duplicates(subset=['suministro', 'pfactura'])

        #retiramos los duplicados del Frame
        df = df[~df[['suministro', 'pfactura']].apply(tuple, axis=1).isin(duplicados[['suministro', 'pfactura']].apply(tuple, axis=1))].copy()

        #obtenemos todos los suministros del Frame Restante, con todos suministros en la BD, y vemos cuales son los nuevos
        array = np.array(df['suministro'].unique().tolist())
        todosSuministros = self.getAllSuministros()
        suministrosNuevos = np.setdiff1d(array, todosSuministros)

        #Obtenemos los suministros nuevos y filtramos una vez mas de Frame
        nuevos = df[df['suministro'].isin(suministrosNuevos)] 
        df = df[~df['suministro'].isin(suministrosNuevos)]


        return duplicados_unicos, nuevos, df

    def obtener_hash_dataframe(self, df):
        """Genera un hash único del DataFrame basado en su contenido."""
        df_string = df.to_csv(index=False)
        return hashlib.md5(df_string.encode()).hexdigest()

    def verificar_dataframe(self, df_nuevo):
        """Verifica si el nuevo DataFrame es igual al anterior guardado en session_state."""
        nuevo_hash = self.obtener_hash_dataframe(df_nuevo)

        if 'dfGeneral' in st.session_state and st.session_state['dfGeneral'] != nuevo_hash:
            st.session_state.clear()
        
        st.session_state['dfGeneral'] = nuevo_hash

    def getDataFu(self, dfContinuos):

        dfContinuos['cantidad'] = dfContinuos.groupby('suministro')['suministro'].transform('count')
        dfContinuos = dfContinuos[['suministro','ciclo','sector','ruta','latitud','longitud','cantidad','pfactura']].copy()
        dfContinuos.loc[:, 'periodo_fin'] = dfContinuos['pfactura'].copy()
        dfContinuos = dfContinuos.rename(columns={'pfactura': 'periodo_inicio'})

        suministros_unicos = dfContinuos['suministro'].unique().tolist()
        dfFU = pd.DataFrame(list(self.collectionFU.find({
            'suministro': {'$in': suministros_unicos}, 
            'estado': 1
        })))
        dfFU = dfFU.drop(columns=['_id'])

        return dfContinuos, dfFU
    
    def analisisSuministros(self, dfOriginal, dfMongo):
        #dfOriginal: Frame filtrado de nuevos y duplicados. Combinamos con los registros de la base de datos
        df_completo = pd.merge(dfOriginal, dfMongo, on='suministro', suffixes=('_nuevo', '_original'), how='outer', indicator=True)

        #Verificamos cambios en ciclo, sector o ruta
        df_completo['cambio'] = (
            (df_completo['ciclo_nuevo'] != df_completo['ciclo_original']) |
            (df_completo['sector_nuevo'] != df_completo['sector_original']) |
            (df_completo['ruta_nuevo'] != df_completo['ruta_original'])
        )

        #Calculamos la distancia entre los coordenadas de lectura con la coordenada en BD
        df_completo['distancia_metros'] = df_completo.apply(lambda row: 
            self.coordenadas.calculoHaversine(row['latitud_nuevo'], row['longitud_nuevo'], row['latitud_original'], row['longitud_original']), 
            axis=1
        )

        #seleccionamos los tipos de datos para darle tratamiento especial a cada uno
        dfRetirados = df_completo[df_completo['_merge'] == 'right_only'].copy()
        dfReincorporados = df_completo[df_completo['_merge'] == 'left_only'].copy()
        dfCambiados = df_completo[(df_completo['_merge'] == 'both') & df_completo['cambio']].copy()
        dfContinuos = df_completo[(df_completo['_merge'] == 'both') & ~df_completo['cambio']].copy()
        return dfRetirados['suministro'].unique().tolist(), dfReincorporados['suministro'].unique().tolist(), dfCambiados, dfContinuos

    def tratamientoDatosSigof(self, dfGeneral):
        resumen = {
            'totalDias':0,
            'totalDuplicados':0,
            'totalNuevos':0,
            'totalRetirados':0,
            'totalReincorporados':0,
            'totalCambiados':0,
            'totalNormal':0,
            'totalSinLectura':0,
            'totalObs':0,
            'resumenObservaciones':0,
        }

        #Verificamos si el df ya esta guardado 
        self.verificar_dataframe(dfGeneral)

        #Eliminamos los suminsitros que hayamos carga dos veces del mismo periodo
        dfGeneral = dfGeneral.drop_duplicates(subset=['suministro', 'pfactura'])

        #Limpiamos las tildes del ciclo
        dfGeneral['ciclo'] = dfGeneral['ciclo'].apply(self.cleandata.corregir_caracteres)
        #realizamos limpieza de la ruta para tenerlo homogenio
        dfGeneral['ruta'] = dfGeneral['ruta'].apply(self.cleandata.cleanRuta)


        #Duplicados: los que YA se encuentran en la base de datos
        #Nuevos: los que NO se encuentran en la base de datos
        #Filtrado: el resto de suministros que evaluaremos
        if ('duplicados' not in st.session_state) or ('nuevos' not in st.session_state) or ('filtrados' not in st.session_state):
            dfDuplicados, dfNuevos, dfFiltrado = self.comprobacion(dfGeneral)
            st.session_state['duplicados'] = dfDuplicados
            st.session_state['nuevos'] = dfNuevos
            st.session_state['filtrados'] = dfFiltrado
        else:
            dfDuplicados = st.session_state['duplicados']
            dfNuevos = st.session_state['nuevos']
            dfFiltrado = st.session_state['filtrados']

        resumen['totalDuplicados'] = len(dfDuplicados)

        dfCompleto = pd.concat([dfFiltrado,dfNuevos], ignore_index=True)
        if len(dfCompleto) <= 0:
            return resumen
        
        #SE CONVIERTE EL CAMPO FECHA A UN FORMATO PARA HACER CALCULOS
        dfCompleto['fecha_ejecucion'] = pd.to_datetime(dfCompleto['fecha_ejecucion'], errors='coerce')
        #SE VERIFICA SI CUMPLIO CON EL CRONOGRAMA
        dfCompleto['cronograma'] = dfCompleto.apply(self.cronograma.verificar_ejecucion, axis=1)
        #SE OBTIENEN LOS DATOS DE LA EJECUCION
        dfFechaEJecucion = dfCompleto[['suministro', 'latitud', 'longitud', 'fecha_ejecucion', 'cronograma']]

        # SE CALCULA EL TOTAL DE DIAS DEL PROCESO, SUMINISTROS QUE NO REGISTRAN LECTURA, Y CUANTAS OBSERVACIONES SE ENCUENTRAN
        fecha_min = dfCompleto['fecha_ejecucion'].min()
        fecha_max = dfCompleto['fecha_ejecucion'].max()
        resumen['totalDias'] = (fecha_max - fecha_min).days
        resumen['totalSinLectura'] = len(dfCompleto[dfCompleto['lectura'].isna() | (dfCompleto['lectura'] == '')])
        resumen['totalObs'] = len(dfCompleto[dfCompleto['obs'].notna() & (dfCompleto['obs'] != '')])

        if 'final' not in st.session_state:
            if len(dfFiltrado) > 0: 
                #Obtenemos todos los registros actuales y de la BD
                if ('original' not in st.session_state) or ('mongo' not in st.session_state):
                    dfOriginal, dfMongo = self.getDataFu(dfFiltrado)
                    st.session_state['original'] = dfOriginal
                    st.session_state['mongo'] = dfMongo
                else:
                    dfOriginal = st.session_state['original']
                    dfMongo = st.session_state['mongo']

                #realizamos una identificacion de tipos de casos
                if ('retirados' not in st.session_state) or ('reincorporados' not in st.session_state) or ('cambiados' not in st.session_state) or ('continuan' not in st.session_state):
                    retirados, reincorporados, dfCambiados, dfContinuan = self.analisisSuministros(dfOriginal, dfMongo)
                    st.session_state['retirados'] = retirados
                    st.session_state['reincorporados'] = reincorporados
                    st.session_state['cambiados'] = dfCambiados
                    st.session_state['continuan'] = dfContinuan
                else:
                    retirados = st.session_state['retirados']
                    reincorporados = st.session_state['reincorporados']
                    dfCambiados = st.session_state['cambiados']
                    dfContinuan = st.session_state['continuan']

                #tratamiento epara retirados
                dfRetirados = dfMongo[dfMongo['suministro'].isin(retirados)]
                resumen['totalRetirados'] = len(dfRetirados)
                st.session_state['dfRetirados'] = dfRetirados

                #Tratamiento para reincorporados
                dfReincorporado = dfOriginal[dfOriginal['suministro'].isin(reincorporados)]
                dfReincorporadoResultado, dfReincorporadoUpdate = self.fichaunica.updateReincorporados(reincorporados, dfReincorporado)
                resumen['totalReincorporados'] = len(dfReincorporadoResultado)
                st.session_state['dfReincorporado'] = dfReincorporadoUpdate

                #tratamiento para los que cambiaron ciclo,sector o ruta
                dfCambiadosResultado, dfCambiadosUpdate, listaCambiadosUpdate = self.fichaunica.updateCambiados(dfCambiados)
                resumen['totalCambiados'] = len(dfCambiadosResultado)
                st.session_state['dfCambiados'] = dfCambiadosUpdate
                st.session_state['listaCambiados'] = listaCambiadosUpdate

                #Tratamiento para el resto de registros
                dfNormalResultado, listaNormal = self.fichaunica.updateNormal(dfContinuan)
                resumen['totalNormal'] = len(dfNormalResultado)    
                st.session_state['listaNormal'] = listaNormal
            else:
                dfReincorporadoResultado = pd.DataFrame()
                dfCambiadosResultado = pd.DataFrame()
                dfNormalResultado = pd.DataFrame()     

            if len(dfNuevos) > 0: 
                if ('nuevosFinal' not in st.session_state):
                    #obtener registros nuevos para ponerle banderas
                    dfNuevosLatLong = dfNuevos[['suministro','ciclo','sector','ruta']].copy()
                    dfNuevosLatLong.columns = ['suministro','ciclo_nuevo','sector_nuevo','ruta_nuevo']
                    dfNuevosLatLong['distancia_metros'] = 0
                    dfNuevosLatLong['bandera_amarilla'] = True
                    dfNuevosLatLong['bandera_roja'] = False
                    resumen['totalNuevos'] = len(dfNuevos)
                    st.session_state['nuevosFinal'] = dfNuevosLatLong
                else:
                    dfNuevosLatLong = st.session_state['nuevosFinal']
            else:
                dfNuevosLatLong = pd.DataFrame()

             #Frame con la evaluacion de Coordenadas
            dfFinal = pd.concat([dfReincorporadoResultado,dfCambiadosResultado,dfNormalResultado, dfNuevosLatLong], ignore_index=True)
            #bandera Blanca para limpiar banderas amarillas
            dfFinal['bandera_blanca'] = False
            #bandera Rosa para limpiar las banderas rojas
            dfFinal['bandera_rosa'] = False   
            st.session_state['final'] = dfFinal

        else:
            dfFinal = st.session_state['final']  

        
        if 'final_final' not in st.session_state:

            # Merge con dfFiltrado
            dfFinal = dfFinal.merge(dfFechaEJecucion, on='suministro', how='left')

            #Evaluamos el tiempo de ejecucion
            dfFinal = self.cronograma.tiempo_ejecucion(dfFinal)

            #observaciones sin FOTO
            dfCompleto['bandera_morada'] = dfCompleto.apply(lambda row: True if pd.notna(row['obs']) and row['foto'] != 'ver foto' else False, axis=1)
            
            #Analisis relecturas
            dfCompleto['relectura'] = dfCompleto['tipo_lectura'] == 'R '
            dfCompleto['debeRelecturarse'] = dfCompleto['obs'].isin([15,21,39])
            st.session_state['dfCompleto'] = dfCompleto
            dfFinal = dfFinal.merge(dfCompleto[['suministro', 'bandera_morada', 'relectura','debeRelecturarse','lecturista']], on='suministro', how='left')

            #esto es para los valores nulos, por el tipo de dato
            dfFinal.loc[dfFinal['fecha_ejecucion'].isna(), 'fecha_ejecucion'] = 1
            dfFinal.loc[dfFinal['fecha_ejecucion'] == 1, 'fecha_ejecucion'] = np.nan
            dfFinal.loc[dfFinal['fecha_ejecucion'].isna(), 'fecha_ejecucion'].convert_dtypes(object)
            st.session_state['final_final'] = dfFinal

        else:
            dfFinal = st.session_state['final_final']


        # dfCopy = dfFinal.copy()
        # exportarDuplicados(dfCopy)
        
        # start_time = time.time()
        dfUltimo, dfPorLecturador, dfPorDia = self.cargaLaboral.evaluarCarga(dfFinal)
        # end_time = time.time()  # ⏱️ Guarda el tiempo final
        # elapsed_time = end_time - start_time  # Calcula la diferencia
        # st.write(f"⏳ Tiempo de ejecución: {elapsed_time:.4f} segundos")

        resumenObservaciones = dfCompleto.pivot_table(
            index='obs_descripcion',  # Columna para las filas
            values='suministro',  # Columna que queremos contar
            aggfunc='count',  # Función de agregación para contar los suministros
            fill_value=0,  # Rellenar con 0 los valores faltantes
            margins=True,  # Añade los totales
            margins_name='Total'
        )

        dfRetirados = st.session_state['dfRetirados']
        dfReincorporado = st.session_state['dfReincorporado']
        dfCambiados = st.session_state['dfCambiados']
        listaCambiados = st.session_state['listaCambiados']
        listaNormal = st.session_state['listaNormal']
        dfCompleto = st.session_state['dfCompleto']

        self.actualizacionBD(dfRetirados, dfReincorporado, dfCambiados, 
                                listaCambiados, listaNormal, 
                                dfCompleto, dfUltimo, dfPorLecturador, dfPorDia)
        
        # st.write(resumenObservaciones)
        #11
        resumen['resumenObservaciones'] = resumenObservaciones
        

        return resumen

    def actualizacionBD(self, dfRetirados=None, dfReincorporados=None, dfCambiados=None, listCambiados=None,
                        listaNormal=None, dfCompleto=None, dfUltimo=None, dfPorLecturador=None, dfPorDia=None):
        
        client = MongoClient()  # o tu conexión personalizada
        session = client.start_session()
        try:
            with session.start_transaction():
                if len(dfRetirados) > 0:
                    print(dfRetirados)
                    self.fichaunica.updateRetirado(dfRetirados, session=session, client=client)

                if len(dfReincorporados) > 0:
                    print(dfReincorporados)
                    self.conexion.guardar_en_mongo(dfReincorporados, 'collectionFU', session=session)

                if len(dfCambiados) > 0:
                    print(dfCambiados)
                    self.conexion.guardar_en_mongo(dfCambiados, 'collectionFU', session=session)

                if len(listCambiados) > 0:
                    print(listCambiados)
                    new_values = {"$set": {
                        "estado": 0,
                        "periodo_fin": self.pfactura.getSecondLastPeriodo()
                    }}
                    self.collectionFU.update_many(
                        {"suministro": {"$in": listCambiados}, 'estado': 1},
                        new_values,
                        session=session
                    )

                if len(listaNormal) > 0:
                    print(listaNormal)
                    self.collectionFU.update_many(
                        {"suministro": {"$in": listaNormal}, 'estado': 1},
                        {'$inc': {'cantidad': 1}},
                        session=session
                    )

                if len(dfCompleto) > 0:
                    print(dfCompleto)
                    self.fichaunica.frecuenciaFotografica(dfCompleto, session=session)
                    self.fichaunica.suministroSinLectura(dfCompleto, session=session)
                    self.conexion.guardar_en_mongo(dfCompleto, 'collectionSigof', session=session)

                if len(dfUltimo) > 0:
                    print(dfUltimo)
                    self.conexion.guardar_en_mongo(dfUltimo, 'collectionResultadoSigof', session=session)

                if len(dfPorLecturador) > 0:
                    print(dfPorLecturador)
                    self.conexion.guardar_en_mongo(dfPorLecturador, 'collectionCargaLaboral', session=session)

                if len(dfPorDia) > 0:
                    print(dfPorDia)
                    self.conexion.guardar_en_mongo(dfPorDia, 'collectionEscaladoRuta', session=session)

        except PyMongoError as e:
            try:
                # Intentamos abortar, pero no forzamos si ya fue abortada
                session.abort_transaction()
            except InvalidOperation:
                print("⚠️ La transacción ya había sido abortada automáticamente.")
            print("❌ Rollback ejecutado por error:", e)
        finally:
            session.end_session()

