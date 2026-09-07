"""Módulo que ofrece funciones para descargar cada fichero o informe necesario en cada proceso. Tratando la escritura de los datos a exportar para que tenga una lectura correcta y segura por el usuario.
CÓDIGO DE ELABORACIÓN PROPIA: influenciado en las prácticas curriculares
"""

import os
import sys
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from osgeo import ogr
import geopandas as gpd
import pandas as pd
import csv
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Config.consts import directorio_resultados, directorio_validacion, formato_output
from Utils.imprimir_mensajes import mostrar_output, mostrar_error, log_message

def descargar_gdf_resultados(gdf_input: gpd.GeoDataFrame, nombre_guardado: str):
    """Descarga como Geopackage (.gpkg) la tabla resultante con sus fijos y cambios en el atributo "estado"
    y con sus relaciones concatenadas por "|" de cada geometría.

    Parámetros:
        gdf_input (gpd.GeoDataFrame): geodataframe de entrada a descargar
        nombre_guardado (str): nombre base (sin sufijo ni prefijo) válido asignado por el usuario
    """
    # https://gdal.org/en/stable/drivers/vector/gpkg.html
    driver = ogr.GetDriverByName('GPKG')
    directorio_output = f"{directorio_resultados}/{nombre_guardado}"
    file_output = f"{directorio_output}/{nombre_guardado}{formato_output['gdf_principal']}" 
    if not os.path.exists(directorio_output):
        os.makedirs(directorio_output)
        tqdm.write(mostrar_output(f"Ruta creada: {directorio_output}"))
    if os.path.exists(file_output):
        driver.DeleteDataSource(file_output)

    gdf_output = gdf_input.copy()
    gdf_output.to_file(file_output, driver= 'GPKG', layer= nombre_guardado)
    tqdm.write(mostrar_output(f"Tabla principal '{formato_output['gdf_principal']}' generada con éxito."))
  
def descargar_resumen_por_relacion(df: pd.DataFrame, directorio_output, nombre_guardado): 
    """Función que guarda un resumen más detallado que el reporte, ya que el resporte combina
    por geometria las relaciones, aquí vienen las relaciones simplificadas agrupadas"""
    coefs = [col for col in df.columns if col.lower().startswith("coef_")]
    atr_resumen = {"cantidad": ("relacion", "count")}
    for coef in coefs:
        atr_resumen[f"min_{coef}"] = (coef, 'min')
        atr_resumen[f"promedio_{coef}"] = (coef, 'mean')
        atr_resumen[f"max_{coef}"] = (coef, 'max')
    # Se agrupa para poder tener por relación RCC8
    resumen = df.groupby('relacion').agg(**atr_resumen)
    resumen['porcentaje'] = (resumen['cantidad'] / len(df)) * 100
    columnas = ['cantidad', 'porcentaje'] + [col for col in resumen.columns if col not in ['cantidad', 'porcentaje']]
    resumen = resumen[columnas]
    cols_float = resumen.select_dtypes(include=['float64', 'float32']).columns
    for col in cols_float:
        # Se convierte a float y se reemplaza '.' por ',' para que en el CSV identifique correctamente el separador decimal
        resumen[col] = resumen[col].apply(lambda x: f"{x:.8f}".replace('.', ',') if pd.notna(x) else "")
            
    if not os.path.exists(directorio_output):
        os.makedirs(directorio_output)
    csv_file = Path(os.path.join(directorio_output, f"estadísticas_{nombre_guardado}.csv"))
    csv_file.unlink(missing_ok=True)
    try:
        resumen.to_csv(csv_file, sep=';', index=True, encoding='utf-8-sig')
        tqdm.write(mostrar_output(f"Archivo '{csv_file}' generado con éxito."))
    except IOError as e:
        tqdm.write(mostrar_error(f"Escritura fallida del archivo: {e}"))
        
def descargar_tablas_secundarias(input_fijos, input_cambios, nombre_guardado, columnas_id):
    """Función que guarda las tablas secundarias en formato CSV:
    - input_fijos: Tabla de resultados de fijos (dataframe)
    - input_cambios: Tabla de resultados de cambios (dataframe)
    - anios: los años comprendidos o números secuenciales correspondientes al par de capas
    - zona: según la zona indicada por el usuario
    """
    directorio_output = f"{directorio_resultados}/{nombre_guardado}"
    if not os.path.exists(directorio_output):
        os.makedirs(directorio_output)
    path_fijos = os.path.join(directorio_output, f"fijos_{nombre_guardado}.csv")
    path_cambios = os.path.join(directorio_output, f"cambios_{nombre_guardado}.csv")
    path_df_completo = os.path.join(directorio_output, f"rcc8_todos_{nombre_guardado}.csv")
    df_completo = pd.concat([input_cambios, input_fijos], ignore_index= True)
    descargar_resumen_por_relacion(df_completo, directorio_output, nombre_guardado)
    for tabla, csv_file_str in zip([input_fijos, input_cambios, df_completo], [path_fijos, path_cambios, path_df_completo]):
        resumen = tabla.copy()
        for col in columnas_id:
            resumen[col] = resumen[col].apply(lambda x: f'="{x}"' if pd.notna(x) and x != "" else x)
        cols_float = resumen.select_dtypes(include=['float64', 'float32']).columns
        for col in cols_float:
            # Se convierte a float y se reemplaza '.' por ',' para que en el CSV identifique correctamente el separador decimal
            resumen[col] = resumen[col].apply(lambda x: f"{x:.8f}".replace('.', ',') if pd.notna(x) else "")
        cabecera_csv = resumen.columns.tolist()
        valores_csv = resumen.to_dict(orient='records')
        csv_file = Path(csv_file_str)
        csv_file.unlink(missing_ok=True)
        try:
            with open(csv_file, mode='w', newline='', encoding='utf-8-sig') as fichero:
                objeto_w = csv.DictWriter(fichero, fieldnames=cabecera_csv, delimiter=';')
                objeto_w.writeheader()
                objeto_w.writerows(valores_csv)
                
            tqdm.write(mostrar_output(f"Archivo '{csv_file}' generado con éxito."))
        except IOError as e:
            tqdm.write(mostrar_error(f"Escritura fallida del archivo: {e}"))

def descargar_reporte(reporte:pd.DataFrame, nombre_guardado:str):
    """Descarga un resumen agrupado de las relaciones combinadas RCC8 que hay en las geometrías

    Parámetros:
        reporte (pd.DataFrame): tabla resumen a descargar
        nombre_guardado (str): nombre base (sin sufijo ni prefijo) válido asignado por el usuario
    """
    #path_reporte = os.path.join(directorio_output, f"reporte_{nombre_guardado}.csv")
    directorio_output = f"{directorio_resultados}/{nombre_guardado}"
    if not os.path.exists(directorio_output):
        os.makedirs(directorio_output)
    csv_file = Path(os.path.join(directorio_output, f"reporte_{nombre_guardado}.csv"))
    csv_file.unlink(missing_ok=True)
    try:
        reporte.to_csv(csv_file, sep=';', index=False, encoding='utf-8-sig')
        tqdm.write(mostrar_output(f"Archivo '{csv_file}' generado con éxito."))
    except IOError as e:
        tqdm.write(mostrar_error(f"Escritura fallida del archivo: {e}"))
            
def descargar_umbrales(umbrales: dict, nombre_guardado: str):
    """Descarga un .txt con los umbrales elegidas por el usuario

    Parámetros:
        umbrales (dict): contiene los umbrales por su nombre y valor
        nombre_guardado (str): nombre base (sin sufijo ni prefijo) válido asignado por el usuario
    """
    txt_file = Path(os.path.join(directorio_resultados, f"umbrales_{nombre_guardado}.txt"))
    try:
        with open(txt_file, mode="w", encoding="utf-8-sig") as file:
            for tipo, valor in umbrales.items():
                file.write(f"- Umbral de tipo {tipo.upper()}: {valor}\n")
        tqdm.write(mostrar_output(f"Archivo de umbrales '{txt_file}' generado con éxito."))
        
    except IOError as e:
        tqdm.write(mostrar_error(f"Error al escribir el archivo de umbrales: {e}"))
        
def descargar_matriz(matriz: pd.DataFrame, nombre_guardado: str):
    directorio_output = f"{directorio_validacion}/{nombre_guardado}"
    if not os.path.exists(directorio_output):
        os.makedirs(directorio_output)
    csv_file = Path(os.path.join(directorio_output, f"matriz_{nombre_guardado}.csv"))
    csv_file.unlink(missing_ok=True)
    try:
        #https://pandas.pydata.org/docs/reference/api/pandas.Index.name.html
        matriz.index.name = "muestra\\resultado"
        matriz.to_csv(csv_file, sep=";", encoding='utf-8-sig')
        #reporte.to_csv(csv_file, sep=';', index=False, encoding='utf-8-sig')
        log_message(f"Archivo '{csv_file}' generado con éxito.", None)
    except IOError as e:
        log_message(f"Escritura fallida del archivo: {e}", "e")