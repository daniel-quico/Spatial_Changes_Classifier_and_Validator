'''
En este SCRIPT estarán las variables globales y que se establecen por defecto.
'''
import os

raiz_proyecto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
directorio_capas = os.path.join(raiz_proyecto, "capas")
directorio_resultados = os.path.join(raiz_proyecto, "resultados_clasificacion")
directorio_muestras = os.path.join(raiz_proyecto,"muestras")
directorio_validacion = os.path.join(raiz_proyecto, "resultados_validacion")
LIMITE_MIN = 2
LIMITE_MAX = 30

formato_output = {"gdf_principal" : '.gpkg', "df_secundario":'.csv'}
formato_input = {'ESRI Shapefile':".shp",
                 'GeoPackage': ".gpkg",
                 'GeoJSON': ".geojson"}

items_capa = ["gdf", "num_orden", "año"]

dimensiones_geom = {1:'Lineal', 2:'Superficie'} 
# 0:'Puntual', -> DEPECRATED

tipos_umbrales = ["igualdad", "within", "contain", "interseccion"]
tipos_umbrales_L = ["igualdad", "solape","within", "contain", "cruce"]
umbrales = {}

col_validacion = {True: "rcc8_resultado", False: "rcc8_muestra"}