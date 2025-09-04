import sys
import os
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import pandas as pd
from pymongo import UpdateOne
from app.controllers.conection import MongoDBConnection
conexion = MongoDBConnection()

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


# collectionLimiteRuta = conexion.get_collection('tblLimiteRuta')
collectionServicio = conexion.get_collection('tblServicioElectrico')
# dfRectangulo = pd.DataFrame(list(collectionLimiteRuta.find()))

# dfRectangulo['ruta'] = dfRectangulo['ruta'].apply(cleanRuta)

# operaciones = [
#     UpdateOne(
#         {"_id": fila["_id"]},
#         {"$set": {"ruta": fila["ruta"]}}
#     )
#     for _, fila in dfRectangulo.iterrows()
# ]

# # Ejecutamos todas las actualizaciones en bloque
# resultado = collectionLimiteRuta.bulk_write(operaciones)

# print(f'Rutas actualizadas: {resultado.modified_count}')


for doc in collectionServicio.find():
    rutas_limpias = [cleanRuta(ruta) for ruta in doc.get("rutas", [])]
    collectionServicio.update_one(
        {"_id": doc["_id"]},
        {"$set": {"rutas": rutas_limpias}}
    )


