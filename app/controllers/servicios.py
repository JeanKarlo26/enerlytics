from controllers.conection import MongoDBConnection
import pandas as pd
import streamlit as st
from pymongo.errors import PyMongoError, InvalidOperation

class ServicioController:
    def __init__(self):
        self.conexion = MongoDBConnection()
        self.collectionFU = self.conexion.get_collection('tblFichaUnica')
        self.collectionSE = self.conexion.get_collection('tblServicioElectrico')
        if  'dfFicha' not in st.session_state:
            self.dfFicha = pd.DataFrame(list(self.collectionFU.find({'estado': 1})))
        else:
            self.dfFicha = st.session_state.dfFicha

        if  'dfServicio' not in st.session_state:
            self.dfServicio = pd.DataFrame(list(self.collectionSE.find()))
        else:
            self.dfServicio = st.session_state.dfServicio

    def guardarServicio(self, servicio):
        self.collectionSE.insert_one(servicio)

    def updateServicio(self, servicio):
        session = self.conexion.client.start_session()
        try:
            with session.start_transaction():
                self.collectionSE.update_many(
                    {"nombre": servicio['nombre']},
                    {"$set": {"rutas": servicio['rutas']}},
                    session=session
                )

                self.collectionFU.update_many(
                    {"ruta": {"$in": servicio['rutas']}},
                    {"$set": {"servicio": servicio['nombre']}},
                    session=session
                )
        except PyMongoError as e:
            try:
                print("abortado")
                session.abort_transaction()
            except InvalidOperation:
                print("⚠️ La transacción ya había sido abortada automáticamente.")
            print("❌ Rollback ejecutado por error:", e)
        finally:
            session.end_session()

        