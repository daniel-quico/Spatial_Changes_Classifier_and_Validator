"""Este módulo sigue los siguientes pasos:
- Establecimiento de umbrales (thresholds), apoyándose en ***terminal_utils.py*** para los umbrales de igualdad, within, contain e intersección (por el momento, un nuevo desarrollo añadirá nuevos umbrales para extender la herramienta a elementos lineales, dimensión 1).
- Solicitud de un nombre válido para los archivos y subcarpetas a generar en ***resultados_clasificacion/***. Apoyándose en ***terminal_utils.py***.
- Tratamiento de las capas disponibles según la configuración realizada en ***leer_capas.py***. Se apoya en ***operaciones_espaciales.py***.
- Normalización de la medida que servirá para el cálculo de los coeficientes. En caso de ser una comparación puramente geométrica se generan IDs automáticos para poder identificar cómo se relaciona cada geometría.

CÓDIGO DE ELABORACIÓN PROPIA: Lógica del flujo y del uso de funciones como helpers
"""


import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tqdm import tqdm

from Config.consts import tipos_umbrales, tipos_umbrales_L, umbrales
from Utils.imprimir_mensajes import mostrar_info, log_message
from Utils.operaciones_espaciales import descartar_comparacion, tratar_capas, comparar_capas_pares
from Utils.terminal_utils import establecer_umbral, obtener_nombre_valido
from Utils.descargar_resultados import descargar_gdf_resultados, descargar_tablas_secundarias, descargar_reporte, descargar_umbrales

def comparar_capas(capas: dict, dim: int):
    # Establecer umbrales 
    tipos_umbrales_def = tipos_umbrales if dim == 2 else tipos_umbrales_L 
    
    for tipo in tipos_umbrales_def:
        if dim == 2 and tipo == "interseccion":
            umbrales[tipo] = establecer_umbral(f"Introduce el valor (de 0 a 0.2) para la tolerancia de tipo {tipo.upper()}: ", maximo=0.2)
            continue
        umbrales[tipo] = establecer_umbral(f"Introduce el valor (de 0.5 a 1) para el umbral de tipo {tipo.upper()}: ", minimo=0.5)
    print()    
    nombre_capa_comparacion = obtener_nombre_valido(f"Escribe el 'nombre' que se le asignará a cada resultado de comparaciones "
                                                    f"[tipo_tabla]_[nombre]_A_B.[ext]: ")
    print()
    
    for capa in capas.values():
        capa["gdf"], capa["tiene_id"] = tratar_capas(capa["gdf"], str(capa["año"] if capa["año"] != -1 else capa["num_orden"]))
        #crear_indice_espacial(capa["gdf"]) DEPECRATED
    
    nombres = list(capas.keys())
    datos = list(capas.values())
    validos = 0
    for i in range(len(datos)-1):
        with tqdm(total=6) as pbar:
            pbar.update(1)
            tqdm.write(mostrar_info(f"Comparando {nombres[i]} con {nombres[i+1]}...", None))
            capa_A = datos[i]
            capa_B = datos[i+1]

            if descartar_comparacion(capa_A["gdf"], capa_B["gdf"]):
                tqdm.write(mostrar_info(f"Capa '{nombres[i]}' no tiene relación alguna con la capa '{nombres[i+1]}'","1"))
                continue
            #print(len(capa_A["gdf"]))
            id_disponible = capa_A["tiene_id"] and capa_B["tiene_id"]
            sub_IDs = [capa_A["num_orden"], capa_B["num_orden"]] if capa_A["año"] == -1 or capa_A["año"] == None else [capa_A["año"], capa_B["año"]]
            
            gdf_principal, df_fijos, df_cambios, reporte_tipos = comparar_capas_pares(capa_A["gdf"], capa_B["gdf"], sub_IDs, umbrales, pbar, id_disponible, dim)
            
            nombre_guardado = f"{nombre_capa_comparacion}_{sub_IDs[0]}_{sub_IDs[1]}"
            columnas_id = [f"ID_{sub_IDs[0]}", f"ID_{sub_IDs[1]}"]
            descargar_gdf_resultados(gdf_principal, nombre_guardado)
            descargar_tablas_secundarias(df_fijos, df_cambios, nombre_guardado, columnas_id)
            descargar_reporte(reporte_tipos, nombre_guardado)
            pbar.update(1)
            validos += 1
            sub_id_1_reporte = f"{sub_IDs[0]}" if validos == 1 else sub_id_1_reporte
                
        descargar_umbrales(umbrales, f"{nombre_capa_comparacion}_{sub_id_1_reporte}_{sub_IDs[1]}") if validos != 0 else log_message("Ninguna capa del conjunto de capas se solapa", None)
