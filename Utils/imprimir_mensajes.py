"""Módulo para imprimir mensajes en la terminal de ejecución
    CÓDIGO DE ELABORACIÓN PROPIA influenciado en las prácticas curriculares
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#from Config.consts import directorio_capas
'''Este SCRIPT se encarga de la Interfaz de Usuario  (UI) en la Terminal.
'''

def mostrar_info(mensaje, modo):
  """Función que imprime en pantalla el mensaje como INFORMACIÓN
  """
  return f">>> {mensaje}" if modo is None else f"<<< {mensaje}"
def pedir_input(mensaje="") -> str:
  """Función que solicita al usuario un input y devuelve su valor correspondiente a una variable
  """
  valor = input(f"-> {mensaje}")
  return valor
def mostrar_output(mensaje):
  """Función que imprime en pantalla el output debido a una acción realizada
  """
  return f"<- {mensaje}"
def mostrar_sugerencia(mensaje):
  """Función que imprime en pantalla un mensaje de sugerencia al usuario
  """
  return f"(i) {mensaje}"

def  mostrar_advertencia(mensaje):
  """Función que imprime un mensaje de advertencia en pantalla
  """
  return f"[ADVERTENCIA] {mensaje}"
  
def mostrar_error(mensaje):
  """Función que imprime en pantalla el error debido a una acción realizada en la ejecución
  """
  return f"[ERROR] {mensaje}"

def log_message(mensaje, modo=""):
  """Imprime en pantalla un mensaje según su tipo:
  - modo = "" : Actúa como mensaje de INPUT pidiendo datos y devolviendo un valor (->)
  - modo = None : Actúa como mensaje de INFO, imprime con >>>
  - modo = "x", siendo x un número: Actúa como mensaje de INFO, imprime con <<<
  - modo = "o" : Actúa como mensaje de OUTPUT (<-)
  - modo = "i": Actúa como mensaje de SUGERENCIA ([i])
  - modo = "a": Actúa como mensaje de ADVERTENCIA ([ADVERTENCIA])
  - modo = "e"-> Actúa como mensaje de ERROR ([ERROR])
  """
  if modo is None or modo.isdigit():
    print(mostrar_info(mensaje, modo))
    return
  if not modo:
    return pedir_input(mensaje)
  if modo == "i":
    print(mostrar_sugerencia(mensaje))
    return
  if modo == "a":
    print(mostrar_advertencia(mensaje))
    return
  print(mostrar_output(mensaje)) if modo == "o" else print(mostrar_error(mensaje), file=sys.stderr)
#log_message(f"{directorio_capas}", None)