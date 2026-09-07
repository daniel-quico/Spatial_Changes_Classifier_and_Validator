import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# https://gis.stackexchange.com/questions/478160/gdal-warning-when-importing-geopandas
#os.environ['GDAL_DATA'] = os.path.join(f'{os.sep}'.join(sys.executable.split(os.sep)[:-1]), 'Library', 'share', 'gdal')
from Utils.leer_archivos_csv import analizar_muestras_resultados
from Utils.calculo_tiempo import establecer_tiempo
from Utils.validar_muestra import validar_clasificacion

def validacion_resultados_muestra():

    resultado, muestra = analizar_muestras_resultados()
    if resultado is not None:
        t_0 = time.perf_counter()
        validar_clasificacion(resultado, muestra)
        establecer_tiempo(time.perf_counter()-t_0)

if __name__ == "__main__":
    validacion_resultados_muestra()