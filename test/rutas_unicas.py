#SCRIPT PARA LIMPIAR LAS RUTAS Y DEJARLAS HOMOGENEAS

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.controllers.conection import MongoDBConnection
from app.controllers.cargaArchivos import CleanData
import streamlit as st
import pandas as pd

from concurrent.futures import ProcessPoolExecutor
from pymongo import UpdateMany
# updates = [
#     UpdateOne({"ruta": row["_id"]}, {"$set": {"ruta": row["ruta_nueva"]}})
#     for _, row in df.iterrows()
# ]

# if updates:  # Asegurar que hay datos antes de actualizar
#     collection.bulk_write(updates)

from multiprocessing import Pool

def actualizar_batch(sub_df, batch_num):
    """Actualiza un lote de datos en MongoDB y muestra progreso."""
    conexion = MongoDBConnection()
    collection = conexion.get_collection('tblFichaUnica')

    updates = [
        UpdateMany({"ruta": row["_id"]}, {"$set": {"ruta": row["ruta_nueva"]}})
        for _, row in sub_df.iterrows()
    ]

    if updates:
        collection.bulk_write(updates)  # ✅ Actualización masiva en MongoDB

    print(f"✔️ Lote {batch_num}: {len(updates)} rutas actualizadas.")

if __name__ == "__main__":

    conexion = MongoDBConnection()
    collection = conexion.get_collection('tblFichaUnica')


    # if 'df' not in st.session_state: 
    pipeline = [
        {"$group": {"_id": "$ruta"}},
        # {"$count": "total_rutas_unicas"}
    ]

    result = list(collection.aggregate(pipeline))
    # print(result)

    # unique_routes = collection.distinct("ruta")
    # st.write(f"Total de rutas únicas: {len(result)}")

    # st.session_state['df'] = 

    df = pd.DataFrame(result)
    st.write(df)

    limpiador = CleanData()
    df['ruta_nueva'] = df['_id'].apply(limpiador.cleanRuta)

    st.write(len(df))
    print('EMPIEZAAAA')

    df = df[df["_id"] != df['ruta_nueva']]

    st.write(len(df))

    ##NO FUNCIONA TAN BIEN 
    num_workers = 20  # Usa 20 núcleos
    chunks = [df.iloc[i::num_workers] for i in range(num_workers)]  # División en lotes

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(actualizar_batch, chunk, i) for i, chunk in enumerate(chunks)]
    print("🚀 Actualización completada utilizando todos los núcleos.")
