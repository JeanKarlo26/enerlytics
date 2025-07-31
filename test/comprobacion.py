import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from app.controllers.conection import MongoDBConnection
import streamlit as st
import pandas as pd

if __name__ == "__main__":

    conexion = MongoDBConnection()
    collection = conexion.get_collection('tblFichaUnica')
    collectionSigof = conexion.get_collection('tblSigof')

    resultado = collectionSigof.distinct("ruta", {"pfactura": 202401})
    cantidad_rutas_distintas = len(resultado)

    resultado2 = collection.distinct("ruta", {"estado": 1})
    cantidad_rutas_distintas2 = len(resultado2)

    st.write(cantidad_rutas_distintas)
    st.write(cantidad_rutas_distintas2)

    resultado = collectionSigof.distinct("suministro", {"pfactura": 202401})
    cantidad_rutas_distintas = len(resultado)
    st.write(cantidad_rutas_distintas)

    resultado2 = collection.distinct("suministro", {"estado": 1})
    cantidad_rutas_distintas2 = len(resultado2)

    st.write(cantidad_rutas_distintas2)

    set_pfactura = set(resultado)
    set_estado = set(resultado2)

    # Diferencia: los que están en pfactura y no en estado
    diferencia = set_estado - set_pfactura

    st.write(f"Suministros en pfactura=202312 que no están en estado=1: {len(diferencia)}")
    st.write(list(diferencia))

