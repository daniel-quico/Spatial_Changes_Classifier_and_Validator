"""Módulo que se encarga de calcular el tiempo de ejecución transcurrido  
CÓDIGO DE ELABORACIÓN PROPIA: Basado en las prácticas curriculares"""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Utils.imprimir_mensajes import log_message
def establecer_tiempo(total_segundos: float) -> str:
    horas = int(total_segundos // 3600)
    minutos =  int((total_segundos % 3600) / 60)
    segundos = int(total_segundos % 60)
    milisegundos = int((total_segundos % 1) * 1000)    
    
    partes_tiempo = []
    if horas > 0:
        partes_tiempo.append(f"{horas}h")
    if minutos > 0 or horas > 0:
        partes_tiempo.append(f"{minutos}min")
    partes_tiempo.append(f"{segundos}.{milisegundos:03d}s")
    tiempo_hh_mm_ss = " ".join(partes_tiempo)
    log_message(f"Proceso finalizado", None)
    log_message(f"Tiempo total de ejecución: {tiempo_hh_mm_ss}", None)