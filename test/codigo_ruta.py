import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from app.controllers.conection import MongoDBConnection
import streamlit as st
import pandas as pd

# def obtener_diccionario_rutas(coleccion):
#     rutas_diccionario = {
#         str(doc['codigo']): f"{doc['descripcion']} - {doc['codigo_ruta']}"
#         for doc in coleccion.find({}, {'codigo': 1, 'descripcion': 1, 'codigo_ruta': 1})
#     }
#     return rutas_diccionario

# def corregir_ruta(df, columna, diccionario):
#     def mapear(valor):
#         partes = str(valor).split(' - ')
#         codigo = partes[0]
#         nuevo_texto = diccionario.get(codigo, partes[-1])
#         return f"{codigo} - {nuevo_texto}"
    
#     df[columna] = df[columna].apply(mapear)
#     return df


if __name__ == "__main__":
    conexion = MongoDBConnection()
    collectionFU = conexion.get_collection('tblFichaUnica')
    collection = conexion.get_collection('tblFotoLectura')
    collectionSigof = conexion.get_collection('tblResultadoSigof')
    # coleccion = pd.DataFrame(list(collection.distinct("ruta", {"estado": 1})))

    # rutas_diccionario = obtener_diccionario_rutas()
    # df = corregir_ruta(df, 'ruta', rutas_diccionario)

    pipeline = [
        {
            "$match": {
                "periodo": 202507
            }
        },
        {
            "$group": {
                "_id": "$suministro",
                "maxFoto": { "$max": "$indicador_foto" },
                "docId": {
                    "$first": "$_id"  # Si quieres el _id del registro con mayor indicador_foto, se puede ajustar
                }
            }
        }
    ]


    registro_max = collection.aggregate([
        {"$match": {"periodo": 202507}},
        {"$sort": {"indicador_foto": -1}},
        # {"$limit": 1}
    ])
    ids_a_conservar = [doc["docId"] for doc in collection.aggregate(pipeline)]


    st.write(len(ids_a_conservar))
    # # st.write(ids_a_conservar)

    
    # suministros_validos = pd.DataFrame(list(collectionSigof.find({"periodo": 202507})))
    # suministros = pd.DataFrame(list(collectionFU.find({"estado": 1})))

    # suministros_validos = collectionSigof.distinct('suministro', {"periodo": 202507})
    # st.write(len(suministros_validos))
    

    # # 2. Actualizar en ficha_unica todos los del periodo 202507 que NO estén en esa lista
    # ss = list(collectionFU.find({
    #         "estado": 1,
    #         "suministro": { "$nin": suministros_validos }
    #     }))
    # st.write(len(ss))
    # resultado = collection.delete_many({
    #     "periodo": 202507,
    #     "suministro": { "$nin": suministros_validos }
    # })



    # pipeline = [
    #     { "$match": { "estado": 1 } },
    #     { "$group": {
    #         "_id": "$suministro",
    #         "count": { "$sum": 1 },
    #         "ids": { "$push": "$_id" }
    #     }},
    #     { "$match": { "count": { "$gt": 1 } } }
    # ]

    # duplicados = list(collectionFU.aggregate(pipeline))

    # # Opcional: extraer todos los documentos duplicados
    # ids_duplicados = [id for grupo in duplicados for id in grupo["ids"]]

    # registros_duplicados = list(collectionFU.find({ "_id": { "$in": ids_duplicados } }))
    # st.write(registros_duplicados)
    # st.write(len(registros_duplicados))
    collection.delete_many({
        "periodo": 202507,
        "_id": { "$nin": ids_a_conservar }
    })





