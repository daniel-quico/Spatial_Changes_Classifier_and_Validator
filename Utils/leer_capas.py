"""Módulo que se encarga de:
- escanear archivos CSV que se ubican en las carpetas de resultados correspondientes. Se apoya en la función *leer_formatos* de ***lectura_formato.py*** para leer los ficheros como 
DataFrame.
- Después se trata con cada tabla para obtener cuantos CSVs fueron válidos en la lectura. En caso de no disponer de mínimo uno de los dos ficheros (CSV de muestra o de resultado) se interrumpe el programa.  
- Dado el caso de éxito, se muestra al usuario cuál de los archivos disponibles para cada tipo (muestra y resultado) quiere usar para la validación.
CÓDIGO DE ELABORACIÓN PROPIA: Influenciado en las prácticas y uso de helpers e interacción con el usuario.

"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Config.consts import directorio_capas, LIMITE_MIN, LIMITE_MAX, formato_input
from Utils.imprimir_mensajes import log_message
from Utils.lectura_formato import leer_formatos, establecer_epsg_tratamiento
from Utils.operaciones_espaciales import analizar_dimensiones_capas
from Utils.operaciones_descriptivas import verificar_atributo_comun, renombrar_atributo_interes
from Utils.herramientas_ui import pedir_confirmacion, escoger_dimension, seleccionar_orden_capas, gestionar_capas_sin_atr_interes

def escanear() -> dict:
    """Función que escanea el directorio **capas/** para cargar las capas como geodataframes
    Returns:
        Dictionary {nombre, gdf}: Diccionario con el nombre del archivo como clave y el geodataframe válido como valor
    """
    if not os.path.exists(directorio_capas):
        log_message(f"La carpeta no existe: {directorio_capas}", "e")
        return {}
    archivos_disponibles = os.listdir(directorio_capas)
    archivos_clasificados = {formato_input['ESRI Shapefile']: [], formato_input['GeoPackage']: [],formato_input['GeoJSON']: []}
    capas_en_sucio = {}
    epsg_final = establecer_epsg_tratamiento()
    for archivo in archivos_disponibles:
        nombre, extension = os.path.splitext(archivo)    
        extension_low = extension.lower()
        if extension_low in formato_input.values():
            capas_en_sucio[nombre] = leer_formatos(nombre, extension_low, epsg_final)
            gdf = capas_en_sucio[nombre]
            if gdf is not None:
                archivos_clasificados[extension_low].append(nombre)
    capas_validas = {nombre: gdf for nombre, gdf in capas_en_sucio.items() if gdf is not None}
    [log_message(f"Capas formato '{ext}': {len(lista_gdfs)} capas procesadas.", "1") for ext, lista_gdfs in archivos_clasificados.items() if lista_gdfs]
 
    if len(capas_validas) < LIMITE_MIN:
        log_message(f"No hay capas suficientes. Mínimo tiene que haber {LIMITE_MIN} capas válidas para poder procesar", "e")
        return {}
    if len(capas_validas) > LIMITE_MAX:
        log_message(f"Hay más capas de lo permitido. Máximo tiene que haber {LIMITE_MAX} capas válidas para poder procesar", "e")
        return {} 
    total_perdidos = f". Total de capas perdidas: {len(capas_en_sucio)-len(capas_validas)}" if len(capas_validas) < len(capas_en_sucio) else ""
    log_message(f"Escaneo finalizado. Total de capas cargadas: {len(capas_validas)}{total_perdidos}", None)
    return capas_validas

def ordenar_capas(capas: dict) -> dict:
    """Función que ordena las capas según las opciones ofrecidas al usuario

    Args:
        capas (dict): capas válidas de entrada a ordenar

    Returns:
        dict: devuelve las capas ordenadas
    """
    nombres_archivos = list(capas.keys())
    log_message("Configuración de archivos y (posibles) años de procesamiento ", None)
    log_message("Selecciona una opción para configurar el orden:"
                "\n    [y] Asignar años después de establecer el orden"
                f"\n    [n] No se asignan años. Solo se establece el orden de comparación manualmente (1-{len(nombres_archivos)})", "i")
    opcion = pedir_confirmacion("¿y/n?: ")
    
    capas_ordenadas = seleccionar_orden_capas(capas, nombres_archivos, opcion)

    return capas_ordenadas

def obtener_id_comparacion(capas: dict):
    opcion = pedir_confirmacion("¿Dispone el conjunto de capas de un atributo en común? y/n: ")
    if opcion == False:
        log_message("Al no haber un atributo en común, la comparación se realizará geometría a geometría", "a")
        return capas
    columna_comun = str(log_message(f"Escribe el nombre del atributo: "))
    
    capas_con_atr_interes, capas_sin_atr_interes = verificar_atributo_comun(capas, columna_comun)
    log_message(f"Capas sin {columna_comun}: {len(capas_sin_atr_interes)}. Capas con {columna_comun}: {len(capas_con_atr_interes)}", None)
    if capas_sin_atr_interes:
        log_message(f"La columna '{columna_comun}' no existe o no es de tipo válido (ni texto ni numérico) en: {', '.join(capas_sin_atr_interes)}", "a")
        respuesta = gestionar_capas_sin_atr_interes()
        if respuesta == "INTERRUMPIR":
            return None
    capas_tratadas = renombrar_atributo_interes(capas, capas_con_atr_interes)
    return capas_tratadas
        
def analizar_capas():
    log_message(f"Escaneando carpeta de origen: {directorio_capas}", None)
    capas_escaneadas = escanear()
    if not capas_escaneadas:
        return None, None
    
    # Despues de leer los ficheros gdfs se decide el orden y se analizan las dimensiones
    dim_elegida = escoger_dimension()
    capas_configuradas = analizar_dimensiones_capas(ordenar_capas(capas_escaneadas), dim_elegida)
    if not capas_configuradas:
        log_message(f"Interrupción de Configuración. No se puede ejecutar el proceso", None)
        return None, dim_elegida
    capas_configuradas_id = obtener_id_comparacion(capas_configuradas)
    return capas_configuradas_id, dim_elegida
