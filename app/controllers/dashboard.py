import pandas as pd
from controllers.conection import MongoDBConnection
import streamlit as st
from controllers.periodo import Pfactura

class DashBoard:
    def __init__(self):
        self.conexion = MongoDBConnection()
        self.pfactura = Pfactura()
        self.collectionLastPeriodo = self.conexion.get_collection('tblLastPeriodo')
        self.collectionResultados = self.conexion.get_collection('tblResultadoFinal')
        self.collectionFichaUnica = self.conexion.get_collection('tblFichaUnica')
        self.collectionFotoLectura = self.conexion.get_collection('tblFotoLectura')
        self.collectionCargaLaboral = self.conexion.get_collection('tblCargaLaboral')
        self.collectionEscaladoRuta = self.conexion.get_collection('tblEscaladoRuta')

    def lastPeriodo(self):
        pipeline = [
            { '$match': { 'estado': 1 }, },
        ]
        resultado = list(self.collectionLastPeriodo.aggregate(pipeline))
        return resultado
    
    def getResultados(self, periodo, ciclo, ruta):
        if ciclo == '-- Todos --':
            return pd.DataFrame(list(self.collectionResultados.find({'periodo': periodo})))
        else:
            if ruta == '-- Todos --':
                return pd.DataFrame(list(self.collectionResultados.find({'periodo': periodo, 'ciclo': ciclo})))
            else:
                return pd.DataFrame(list(self.collectionResultados.find({'periodo': periodo, 'ciclo': ciclo, 'ruta': ruta})))
            
    def getFrecuenciaFotoLectura(self, periodo, ciclo, ruta):
        if ciclo == '-- Todos --':
            return pd.DataFrame(list(self.collectionFotoLectura.find({'periodo': periodo})))
        else:
            if ruta == '-- Todos --':
                return pd.DataFrame(list(self.collectionFotoLectura.find({'periodo': periodo, 'ciclo': ciclo})))
            else:
                return pd.DataFrame(list(self.collectionFotoLectura.find({'periodo': periodo, 'ciclo': ciclo, 'ruta': ruta})))
            
    def getCargaLaboral(self, periodo):
        return pd.DataFrame(list(self.collectionCargaLaboral.find({'periodo': periodo})))
            
    def getEscaladoRuta(self, periodo, ciclo, ruta):
        if ciclo == '-- Todos --':
            return pd.DataFrame(list(self.collectionEscaladoRuta.find({'periodo': periodo})))
        else:
            if ruta == '-- Todos --':
                return pd.DataFrame(list(self.collectionEscaladoRuta.find({'periodo': periodo})))
            else:
                return pd.DataFrame(list(self.collectionEscaladoRuta.find({'periodo': periodo, 'ruta': ruta})))