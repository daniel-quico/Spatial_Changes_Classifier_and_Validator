import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# https://gis.stackexchange.com/questions/478160/gdal-warning-when-importing-geopandas
os.environ['GDAL_DATA'] = os.path.join(f'{os.sep}'.join(sys.executable.split(os.sep)[:-1]), 'Library', 'share', 'gdal')

from Utils.leer_capas import analizar_capas
from Utils.comparacion_capas import comparar_capas 
from Utils.calculo_tiempo import establecer_tiempo
def comparacion_bajo_umbral():

    capas, dim = analizar_capas()
    if capas is not None:
        t_0 = time.perf_counter()
        comparar_capas(capas, dim)
        establecer_tiempo(time.perf_counter()-t_0)

if __name__ == "__main__":
    comparacion_bajo_umbral()