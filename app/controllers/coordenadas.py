import numpy as np
import pandas as pd

class Coordenadas:
    def __init__(self):
        pass

    def calculoHaversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Radio de la Tierra en kilómetros
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        return R * c * 1000
    
    def calcular_distancia(self, row):
        lat_nuevo = row['latitud_nuevo']
        lon_nuevo = row['longitud_nuevo']
        lat_orig = row['latitud_original']
        lon_orig = row['longitud_original']

        # Caso 1: Todas las coordenadas son None
        if pd.isna(lat_nuevo) and pd.isna(lon_nuevo) and pd.isna(lat_orig) and pd.isna(lon_orig):
            return 99999

        # Caso 2: Coordenadas originales faltan → copiar de las nuevas
        elif pd.isna(lat_orig) or pd.isna(lon_orig):
            row['latitud_original'] = lat_nuevo
            row['longitud_original'] = lon_nuevo
            return 99

        # Caso 3: Coordenadas nuevas faltan → dejar en blanco y asignar 999
        elif pd.isna(lat_nuevo) or pd.isna(lon_nuevo):
            row['latitud_nuevo'] = None
            row['longitud_nuevo'] = None
            return 999

        # Caso 4: Todas las coordenadas están presentes → calcular distancia
        else:
            return self.calculoHaversine(lat_nuevo, lon_nuevo, lat_orig, lon_orig)