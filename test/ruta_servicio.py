import pandas as pd
import streamlit as st
import sys
import os
import re
from concurrent.futures import ThreadPoolExecutor
import math

def cleanRuta(text):
    # Corrección de codificaciones mal interpretadas
    replacements = {
        'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
        'Ã': 'Á', 'Ã‰': 'É', 'Ã': 'Í', 'Ã“': 'Ó', 'Ãš': 'Ú',
        'BAÃ?OS': 'BAÑOS'
    }
    for v, k in replacements.items():
        text = text.replace(v, k)

    # Convertir a mayúsculas
    text = text.upper()

    # Eliminar puntos
    text = re.sub(r'\.', '', text)

    # Normalizar guiones
    text = re.sub(r'\s*-\s*', ' - ', text)
    text = re.sub(r'-\s*$', '', text)

    # Reemplazar abreviaciones
    abreviaciones = {
        r'\bCAS\b': 'CASERIO',
        r'\bBQ\b': 'BLOQUE',
        r'\bCPMA\b': 'CENTRO POBLADO MAYOR',
        r'\bCPMEN\b': 'CENTRO POBLADO MENOR',
        r'\bCPME\b': 'CENTRO POBLADO MENOR',
        r'\bCPM\b': 'CENTRO POBLADO MAYOR',
        r'\bCP\b': 'CENTRO POBLADO',
        r'\bCARR\b': 'CARRETERA',
        r'\bURB\b': 'URBANIZACION',
        r'\bBARR\b': 'BARRIO',
        r'\bPBLO\b': 'PUEBLO',
    }
    for pattern, replacement in abreviaciones.items():
        text = re.sub(pattern, f' {replacement} ', text)

    # Consolidar espacios
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

# df = pd.read_excel('ruta_servicio.xlsx')
# df['ruta'] = df['ruta'].apply(cleanRuta)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from app.controllers.conection import MongoDBConnection

def procesar_doc(doc):
    ruta_original = doc.get("ruta", "")
    ruta_limpia = cleanRuta(ruta_original)
    if ruta_original != ruta_limpia:
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"ruta": ruta_limpia}}
        )

if __name__ == "__main__":
    conexion = MongoDBConnection()
    collection = conexion.get_collection('tblLimiteRuta')

    # batch_size = 1000
    # cursor = collection.find({}, {"_id": 1, "ruta": 1})

    # batch = []
    # for doc in cursor:
    #     ruta_original = doc.get("ruta", "")
    #     ruta_limpia = cleanRuta(ruta_original)
    #     if ruta_original != ruta_limpia:
    #         batch.append({
    #             "filter": {"_id": doc["_id"]},
    #             "update": {"$set": {"ruta": ruta_limpia}}
    #         })

    #     # Ejecutar por lote
    #     if len(batch) >= batch_size:
    #         for item in batch:
    #             collection.update_one(item["filter"], item["update"])
    #         batch = []

    # # Procesar lote final
    # for item in batch:
    #     collection.update_one(item["filter"], item["update"])

    def procesar_lote(lote_docs):
        for doc in lote_docs:
            ruta_original = doc.get("ruta", "")
            ruta_limpia = cleanRuta(ruta_original)
            if ruta_original != ruta_limpia:
                collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"ruta": ruta_limpia}}
                )

    # Obtener todos los documentos
    cursor = collection.find({}, {"_id": 1, "ruta": 1})
    docs = list(cursor)

    # Dividir en lotes
    batch_size = 1000
    total_batches = math.ceil(len(docs) / batch_size)
    batches = [docs[i * batch_size:(i + 1) * batch_size] for i in range(total_batches)]

    # Procesar lotes en paralelo
    with ThreadPoolExecutor(max_workers=16) as executor:
        executor.map(procesar_lote, batches)






        # print(f"Servicio: {servicio} → Documentos actualizados: {resultado.modified_count}")

    
