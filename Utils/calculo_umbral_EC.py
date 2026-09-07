"""Módulo de cálculo del umbral para EC, debido a que por lógica hay muchos datos colindantes y que son la mayoría muy próximos a 0
CÓDIGO DE ELABORACIÓN PROPIA basándome en el rango intercuartílico"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import geopandas as gpd
def calcular_umbral(gdf: gpd.GeoDataFrame):
    """Calcula bajo el Criterio de Tukey un umbral para la decisión de mi clasificación de EC"""
    data = gdf['coef_interseccion']
    q1 = data.quantile(0.25)
    q3 = data.quantile(0.75)
    iqr = q3 - q1
    umbral_tukey = q3 + 3 * iqr
    return umbral_tukey