import sys
import os
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import pandas as pd
from pymongo import UpdateOne
from app.controllers.conection import MongoDBConnection
conexion = MongoDBConnection()

def cleanRuta(text):
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

collectionLimiteRuta = conexion.get_collection('tblLimiteRuta')
dfRectangulo = pd.DataFrame(list(collectionLimiteRuta.find()))

dfRectangulo['ruta'] = dfRectangulo['ruta'].apply(cleanRuta)

operaciones = [
    UpdateOne(
        {"_id": fila["_id"]},
        {"$set": {"ruta": fila["ruta"]}}
    )
    for _, fila in dfRectangulo.iterrows()
]

# Ejecutamos todas las actualizaciones en bloque
resultado = collectionLimiteRuta.bulk_write(operaciones)

print(f'Rutas actualizadas: {resultado.modified_count}')

