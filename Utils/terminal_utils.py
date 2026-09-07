"""Módulo para interacciones con el usuario más manuales:
- pedir_confirmacion(msj)
- escoger_dimension()
- escoger_archivo(archivos, msj)
- seleccionar_orden_capas(capas, nombres_archivos, opcion)
- gestionar_capas_sin_atr_interes()
- establecer_umbral(msj, minimo, maximo)
- obtener_nombre_valido(msj)

CÓDIGO DE ELABORACIÓN PROPIA: de la lógica de negocio. E influencia en el uso de otras herramientas para la interacción del usuario con la terminal. Para 
ello se adaptó al uso de librerías en relación a ello: InquirerPy y pathvalidate
"""

import os, sys
from InquirerPy import inquirer
from InquirerPy.base import Choice
from pathvalidate import ValidationError, validate_filename, sanitize_filename
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Utils.imprimir_mensajes import log_message
from Config.consts import dimensiones_geom, items_capa

def pedir_confirmacion(msj: str = "¿Deseas continuar?"):
    """Manejo de ¿y/n? con el usuario"""
    opcion =""
    while opcion.lower() not in ["y", "n","yes","no"]:
        opcion = "".join(log_message(f"{msj}").split()).lower()
    return True if opcion in ["y", "yes"] else False

def escoger_dimension():
    """Manejo de opciones por dimensión, para obtener la dimensión elegida por el usuario"""
    dim_opciones = [Choice(value = dim, name = f"Dimensión {dim}: Elementos {tipo+"es" if dim !=2 else "de "+tipo}")
                        for dim, tipo in dimensiones_geom.items()]
    dim_elegida = inquirer.select(
            message=f"Selecciona la dimensión de comparación de capas:",
            choices=dim_opciones).execute()
    
    return dim_elegida

def escoger_archivo(archivos:list, msj:str):
    """Manejo de las archivos disponibles en la carpeta de archivos"""
    opciones = [Choice(value= i, name= archivos[i]["nombre"])  for i in range(len(archivos))]
    archivo_elegido = inquirer.select(
            message=f"Selecciona el archivo {msj}:",
            choices=opciones).execute()
    return archivo_elegido

def seleccionar_orden_capas(capas: dict, nombres_archivos: list, opcion: bool):
    """Manejo del orden de capas según la interacción del usuario con las capas.  
    Si el usuario decidió no asignar años:
    - Se selecciona con ENTER las capas en cada iteración ordenándose de esa manera
    
    Si el usuario decidió asignas años:
    - Se da un paso extra en cada iteración, no solo se ordena sino que se teclea el año bajo unas condiciones

    Si en la primera iteración decidió CANCELAR (en el resto de iteraciones ya no aparece):
    - Se ordenan por defecto como aparecen de arriba a abajo las capas
      
    **Raises:**
        ValueError: en caso de que se elija la opción de **establecer año** si no se teclea
        un valor numérico, o no tiene 4 dígitos o es vacío
    
    **Returns:**
        dict: capas ordenadas según el caso
    """
    capas_ordenadas = {}
    salida_forzada =  False
    # OPCION Y NOMBRE_ARCHIVOS COMO PARAMETROS
    while nombres_archivos:
        posicion = len(capas_ordenadas) + 1
        
        # Se elige el nombre del fichero que va en el orden de su iteración
        archivo_elegido = inquirer.select(
            message=f"Selecciona el archivo para la posición {posicion}:",
            choices=nombres_archivos + ["CANCELAR: se aplica el orden por defecto"] if posicion == 1 else nombres_archivos,
        ).execute()
        
        if "CANCELAR" in archivo_elegido:
            log_message("Selección manual del orden cancelado. Se acepta el orden por defecto de las capas", "o")
            salida_forzada = True
            break
        ano_guardar = -1
        
        if opcion == True:
            while True:
                try:
                    ano_elegido = log_message(f"Introduce el año (4 dígitos) para '{archivo_elegido}': ")
                    
                    # Se comprueba la validación del año escrito
                    if not ano_elegido.isdigit() or len(ano_elegido) != 4:
                        raise ValueError("El año debe tener exactamente 4 dígitos numéricos.")
                    
                    # Si todo es correcto, se convierte a entero y se sale del bucle
                    ano_guardar = int(ano_elegido)
                    break
                    
                except (ValueError, Exception) as e:
                    # Captura tanto si se deja vacío como si no cumple los 4 dígitos
                    print(f"\n[!] Error: {e} Por favor, inténtalo de nuevo.\n")

        # Se guarda en un diccionario que ya viene ordenado
        capas_ordenadas[archivo_elegido] = {
            items_capa[0]: capas[archivo_elegido],
            items_capa[1]: posicion,
            items_capa[2]: ano_guardar #if opcion =="y" else -1
        }
        
        # Se quita de opciones ya que ya ha sido elegido el fichero y se muestran los restantes
        nombres_archivos.remove(archivo_elegido)
   
    if salida_forzada:
        gdfs = list(capas.values())
        capas_ordenadas = {nombre:{items_capa[0]: gdf, items_capa[1]: orden_defecto, items_capa[2]: None} for nombre, gdf, orden_defecto in zip(nombres_archivos, gdfs, range(1,len(gdfs)+1))}
    return capas_ordenadas

def gestionar_capas_sin_atr_interes():
    """Maneja el flujo si:
    - continuar con una comparación por geometría y no por un atributo descriptivo
    - o interrumpir la ejecución del programa para que el usuario prepare bien los datos
    """
    opciones = [Choice(value= "CONTINUAR", name= "CONTINUAR aún sabiendo que no tiene el atributo de interés (la comparación con estas capas será geometría a geometría)"),
                            Choice(value= "INTERRUMPIR", name = "INTERRUMPIR ejecución para normalizar los datos")]
    respuesta = inquirer.select(message=f"Selecciona cómo deseas proceder:", choices=opciones).execute()
    
    if respuesta == "INTERRUMPIR":
        log_message("Ejecución interrumpida. Por favor, prepara los datos correctamente.", None)    
    return respuesta

def establecer_umbral(msj: str, minimo = 0.0, maximo = 1.0):
    """Manejo de los umbrales con el usuario"""
    while True:
        valor_introducido = log_message(msj)
        try:
            valor = float(valor_introducido)
            if minimo <= valor <= maximo:
                return valor    
            log_message(f"El valor del umbral debe estar entre {minimo} y {maximo}", "e")
        except ValueError:
            log_message("Introduce un número decimal válido (el separador es el '.')", "e")

def obtener_nombre_valido(msj: str) -> str:
    """Obtención del nombre válido para los resultados de cada comparación"""
    # https://www.tradingcode.net/python/validate-check-filename/?__cf_chl_tk=rl.IP1ypWkKryO8sUzZP.OtqlwaSpJH55pFCUV.6c8Y-1783949410-1.0.1.1-MQclKEW5ph4O.YqBHHOoziZdv5w1.xeQKLva52N9W1g
    while True:
        nombre = log_message(msj)
        
        if not nombre.strip():
            log_message("Introduce un nombre válido, no lo dejes vacío ni escribas solo espacios", "e")
            continue
        
        try:
            validate_filename(nombre)
            nombre_valido = nombre
            log_message("El nombre introducido es válido", "o")
        except ValidationError:
            nombre_valido = str(sanitize_filename(nombre))
            
            if not nombre_valido.strip():
                log_message("Los caracteres introducidos no producen un nombre válido. Inténtalo de nuevo", "e")
                continue
            
            log_message(f"Nombre previo a corrección: {nombre}","1")
        
        log_message(f"Nombre definitivo: {nombre_valido}", "1")
        break
    return nombre_valido
