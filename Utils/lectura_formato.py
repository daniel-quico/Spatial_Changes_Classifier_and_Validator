"""Módulo que puede tratar con el formato del input escaneado (2). Como de tratar con un EPSG válido (1)
1. establecer_epsg_tratamiento(msg):  
    **- ELABORACIÓN PROPIA** de la lógica para obtener un EPSG que cumpla con las condiciones del programa  
    **- CÓDIGO ADAPTADO (CRS pyproj 3.7.2 documentation):** https://py.geocompx.org/06-reproj y https://pyproj4.github.io/pyproj/stable/api/crs/crs.html. 
        Para el tratamiento de CRS mediante la librería pyproj en este módulo
        (en vez de tener que programar manualmente para que el numero de digitos coincida con el correspondiente a un EPSG proyectado)  
    **- Líneas posibles futuras /TransformerGroup):** https://pyproj4.github.io/pyproj/stable/api/transformer.html. 
        Uso de TransformerGroup para la transformación de coordenadas  
      
      
2. leer_formatos(file_name, file_ext, epsg_final, es_resultado = False, directorio = None):
    **- ELABORACIÓN PROPIA** de la lógica para tratar con las capas de entrada como archivos CSV
    **- ELABORACIÓN PROPIA:** UI y tratamiento de Errores adaptado a lo aprendido en las prácticas curriculares
    **- FRAGMENTO DE CÓDIGO CONSULTADO A LA IA:** en el filtrado de las cadenas de texto en filas 78 y 80
"""

import sys
import os
import pandas as pd
import geopandas as gpd
from pyproj import CRS
#from pyproj.transformer import TransformerGroup

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Config.consts import directorio_capas, formato_input, col_validacion
from Utils.imprimir_mensajes import log_message
from Utils.terminal_utils import pedir_confirmacion

def establecer_epsg_tratamiento(msg:str = "") -> CRS:
    while True:
        try:
            epsg_destino = log_message("Establezca el código EPSG numérico de tratamiento (debe ser proyectado): ")
            crs_destino = CRS.from_user_input(int(epsg_destino))
        except Exception as e:
            log_message(f"El código EPSG proporcionado no es válido: {e}", "e")
            continue
        if not crs_destino.is_projected:
            log_message(f"El SRC ({crs_destino}) proporcionado{msg} no es un sistema proyectado.\n"
                        "Se recomienda transformar la capa a un EPSG proyectado", "e")
            continue
        log_message(f"{crs_destino} aceptado como CRS{msg}", "1")
        break
    return crs_destino

def leer_formatos(file_name, file_ext, epsg_final, es_resultado = False, directorio = None) -> gpd.GeoDataFrame | pd.DataFrame | None:
    if directorio is None:
        gdf_path = os.path.join(directorio_capas, f"{file_name}{file_ext}")
        try:
            gdf = gpd.read_file(gdf_path)
        except Exception as e:
            log_message(f"Error al leer el archivo {file_name}: {e}", "e")
            return None
        if gdf.empty:
            log_message(f"La capa {file_name} está vacía", "o")
            return None
        if gdf.crs is None:
            msj_adicional = "(.prj inexistente)" if file_ext == formato_input['ESRI Shapefile'] else ""
            log_message(f"No existe un CRS asociado a la capa {file_name} {msj_adicional}", "e")
            opcion = pedir_confirmacion("¿Conoces la proyección de la capa? ¿y/n?: ")
            
            if opcion == True:
                epsg_nuevo = establecer_epsg_tratamiento(f" a la capa '{file_name}{file_ext}'")
                gdf = gdf.set_crs(f"epsg:{epsg_nuevo}")
            else:
                log_message(f"Se desconoce el código EPSG correspondiente a la capa '{file_name}{file_ext}': {e}", "e")
                return None
        if gdf.crs != epsg_final:
            gdf = gdf.to_crs(epsg_final)
        return gdf
    else:
        df_path =  os.path.join(directorio, f"{file_name}{file_ext}")
        try:
            cabecera = pd.read_csv(df_path, sep=";", nrows=0)
            dtype_ids = {col: str for col in cabecera.columns}
            df = pd.read_csv(df_path, sep=";", decimal=",", dtype=dtype_ids)
            cols_id = [col for col in df.columns if col.lower().startswith("id_")]
            for col in cols_id:
                df[col.upper()] = df[col].astype(str).str.replace(r'^[="]+|["]+$', '', regex=True)
            col_nueva = col_validacion[es_resultado]
            df[col_nueva] = df["relacion"].str.split(r"[:]").str[0].str.strip()
            
        except Exception as e:
            log_message(f"Error al leer el archivo {file_name}: {e}", "e")
            return None
        if df.empty:
            msj = f"La muestra {file_name} está vacía" if not es_resultado else f"El resultado {file_name} está vacío"
            log_message(msj, "o")
            return None
        return df
    
