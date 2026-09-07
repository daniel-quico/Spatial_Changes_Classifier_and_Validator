"""Módulo para leer los archivos correspondientes a la muestra y al resultado de clasificación:
    - escanear(es_resultado):  
        **ELABORACIÓN PROPIA** (influenciada en experiencias propias) en la lógica de desarrollo UI  
        **CÓDIGO ADAPTADO (os.walk() in Python):** https://www.geeksforgeeks.org/python/os-walk-python/  
    - analizar_muestras_resultados():
        **ELABORACIÓN PROPIA** en la lógica de desarrollo UI.
        **CÓDIGO ADAPTADO en cuanto al uso de librerías en otros módulos para ofrecer una correcta UI
"""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Config.consts import directorio_muestras, directorio_resultados
from Utils.herramientas_ui import escoger_archivo
from Utils.imprimir_mensajes import log_message
from Utils.lectura_formato import leer_formatos
    
def escanear(es_resultado: bool) -> dict:
    directorio = directorio_resultados if es_resultado else directorio_muestras
    log_message(f"Escaneando carpeta de origen: {directorio}", None)
    if not os.path.exists(directorio):
            log_message(f"La carpeta no existe: {directorio}", "e")
            return {}

    archivos = {}
    for ruta_actual, subcarpetas, ficheros in os.walk(directorio):
        for archivo in ficheros:
            nombre, extension = os.path.splitext(archivo)
            if extension.lower() == ".csv":
                carpeta_archivo = os.path.join(ruta_actual)
                if es_resultado and not nombre.lower().startswith("rcc8"):
                    continue
                archivos[nombre] = leer_formatos(nombre, extension, None, es_resultado, carpeta_archivo)
    archivos_limpios = []
    archivos_limpios = [{"nombre":nombre, "df":df} for nombre, df in archivos.items() if df is not None]
    if not archivos_limpios:
        log_message(f"No hay archivos suficientes. Mínimo tiene que haber 1 archivo en '{carpeta_archivo}' para poder validar", "e")
        return {}
    total_perdidos = f". Total de archivos perdidos: {len(archivos)-len(archivos_limpios)}" if len(archivos) < len(archivos_limpios) else ""
    log_message(f"Escaneo finalizado. Total de archivos cargados: {len(archivos_limpios)}{total_perdidos}", None)
    return archivos_limpios

def analizar_muestras_resultados():
    muestras_escaneadas = escanear(es_resultado= False) # son los unicos csvs en la carpeta de muestras/
    resultados_escaneados = escanear(es_resultado= True) # puede tener fijos.csv cambios.csv y rcc8_total.csv. Interesa solo el tercero, ubicados en resultados/
    if not muestras_escaneadas or not resultados_escaneados:
        return None, None
    muestra_elegida = escoger_archivo(muestras_escaneadas, "de muestra")
    resultado_elegido = escoger_archivo(resultados_escaneados, "de validación")
    return resultados_escaneados[resultado_elegido], muestras_escaneadas[muestra_elegida]
