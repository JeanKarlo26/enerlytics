import streamlit as st
from controllers.conection import MongoDBConnection

class Pfactura:
    def __init__(self):
        self.conexion = MongoDBConnection()
        self.collectionSigof = self.conexion.get_collection('tblSigof')
        self.collectionFU = self.conexion.get_collection('tblFichaUnica')
        self.collectionLast = self.conexion.get_collection('tblLastPeriodo')

    def getLastPeriodo(self):
        if 'lastPeriodo' not in st.session_state:
            listSigof = list(self.collectionLast.find({'estado': 1}))
            st.session_state.lastPeriodo = listSigof[0]['periodo']

        return st.session_state.lastPeriodo
    
    def getSecondLastPeriodo(self):
        listSigof = list(self.collectionLast.find().sort('periodo', -1).skip(1).limit(1))
        return listSigof[0]['periodo'] if listSigof else None
    
    def updateLastPeriodoState(self):
        listSigof = list(self.collectionLast.find({'estado': 1}))
        st.session_state.lastPeriodo = listSigof[0]['periodo']
    
    def getLastPeriodoSigof(self):
        if 'newLastPeriodo' not in st.session_state:
            pipeline = [{
                "$group": {
                    "_id": None,
                    "max_pfactura": {"$max": "$pfactura"}
            }}]

            lista = list(self.collectionSigof.aggregate(pipeline))

            st.session_state.newLastPeriodo = lista[0]["max_pfactura"]

        return st.session_state.newLastPeriodo
    
    def verificarPeriodo(self):
        if self.getLastPeriodoSigof() >= self.getLastPeriodo():
            return True
        return False
    
    def updateLastPeriodo(self):
        query = {"estado": 1}
        new_values = {"$set": {"estado": 0}}
        self.collectionLast.update_many(query, new_values)

    def verifyCondition(self):
        umbral = 1000
        pfactura = self.getLastPeriodo()
        totalRegistros = self.collectionSigof.count_documents({'pfactura': pfactura})
        lastPfactura = self.getLastPeriodoSigof()
        totalRegistrosLast = self.collectionSigof.count_documents({'pfactura': lastPfactura})

        if totalRegistrosLast <= (totalRegistros + umbral) and totalRegistrosLast >= (totalRegistros - umbral):
            return 1
        return 0
        
    def saveNewPeriodo(self):
        condition = self.verifyCondition()
        estado = 1 if condition == 1 else 0

        data = {
            'periodo' : self.getLastPeriodoSigof(),
            'estado' : estado,
            'condicion' : condition
        }

        self.collectionLast.insert_one(data)

    def updatePeriodo(self):
        self.updateLastPeriodo()
        self.saveNewPeriodo()
        self.updateLastPeriodoState()