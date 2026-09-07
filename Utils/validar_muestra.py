import os
import sys
from sklearn.metrics import classification_report
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Utils.imprimir_mensajes import log_message
from Utils.operaciones_descriptivas import obtener_matriz_confusion
from Utils.descargar_resultados import descargar_matriz
from Utils.terminal_utils import obtener_nombre_valido
def validar_clasificacion(resultado: dict, muestra: dict):
    nombre_validacion= obtener_nombre_valido(f"Escribe el 'nombre' que se le asignará a los resultados de validación entre muestra y resultado clasificado "
                                                        f"[objeto]_[nombre].[csv]: ")
    # https://www.geeksforgeeks.org/python/pandas-crosstab-function-in-python/
    # Matriz de confusión
    matriz, df_cruzado, msj, modo_msj = obtener_matriz_confusion(resultado["df"], muestra["df"])
    log_message(msj, modo_msj)
    if matriz is None:
        return
    log_message("Métricas de evaluación de la clasificación","o")
    # https://scikit-learn.org/stable/modules/model_evaluation.html#classification-metrics
    # https://scikit-learn.org/stable/modules/generated/sklearn.metrics.classification_report.html
    print(classification_report(df_cruzado["rcc8_muestra"], df_cruzado["rcc8_resultado"]))
    descargar_matriz(matriz, nombre_validacion)
