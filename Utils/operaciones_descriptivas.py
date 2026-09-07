import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd

# FUNCIONES QUE SE USAN EN leer_capas.py
def verificar_atributo_comun(capas: dict, columna_comun: str):
    capas_con_columna=[]
    capas_sin_columna=[]
    columna_comun = "".join(columna_comun.split()).lower()
    for nombre, datos in capas.items():
            gdf = datos["gdf"]
            
            columnas_gdf = {col.lower(): col for col in gdf.columns}
            # https://pandas.pydata.org/docs/reference/arrays.html#data-type-introspection
            if columna_comun in columnas_gdf.keys():
                col_gdf = columnas_gdf[columna_comun]
                es_numerico = pd.api.types.is_numeric_dtype(gdf[col_gdf])
                es_texto = pd.api.types.is_string_dtype(gdf[col_gdf])
                
                if es_numerico or es_texto:
                    capas_con_columna.append((nombre, col_gdf))
                else:
                    capas_sin_columna.append(nombre)
            else:
                capas_sin_columna.append(nombre)
    return capas_con_columna, capas_sin_columna
   
   
def renombrar_atributo_interes(capas: dict, capas_con_columna: list):
    for nombre, col_gdf in capas_con_columna:
        gdf = capas[nombre]["gdf"]
        # controlar si existe ya una variable llamada ID y no es el que interesa
        if "ID" in gdf.columns and col_gdf != "ID":
            gdf = gdf.rename(columns={"ID": "ID_anterior"})

        gdf = gdf.rename(columns={col_gdf: "ID"})
        gdf["ID"] = gdf["ID"].astype(str)
        capas[nombre]["gdf"] = gdf    
    return capas


# FUNCIONES QUE SE USAN EN operaciones_espaciales.py
def agrupar_descripciones(descripciones: pd.Series, id_disponible: bool) -> str:

    descripciones = list(set(descripciones))
    
    def ordenar_por_tipo(descripcion):
        if descripcion.startswith("EQ"): return 0
        if descripcion.startswith("TPP"): return 1
        if descripcion.startswith("PO"): return 2
        if descripcion.startswith("EC"): return 3
        return 4
    # https://www.w3schools.com/python/ref_func_sorted.asp
    if not id_disponible:
        return " | ".join(sorted(descripciones, key=ordenar_por_tipo))
    
    # [relacion_rcc8]. ID_[X] es nuevo
    desc_con_nuevo = [texto for texto in descripciones if ". ID_" in texto]
    sufijo_nuevo =""
    if desc_con_nuevo:
        posicion = desc_con_nuevo[0].find(". ID_")
        sufijo_nuevo = desc_con_nuevo[0][posicion:]
            
        descripciones = [texto.split(". ID_")[0] for texto in descripciones]
    return " | ".join(sorted(descripciones, key=ordenar_por_tipo)) + sufijo_nuevo

# FUNCIÓN DE APOYO PARA obtener_matriz_confusion
def comprobar_compatibilidad_tablas(df_resultado: pd.DataFrame, df_muestra: pd.DataFrame):
    # Comprobar que las columnas se llaman igual
    cols_id_resultado = set(col for col in df_resultado.columns if col.startswith("ID_"))
    cols_id_muestra = set(col for col in df_muestra.columns if col.startswith("ID_"))
    if cols_id_resultado != cols_id_muestra:
        return False, [], f"Las columnas ID no coinciden. Resultado: {list(cols_id_resultado)}, Muestra: {list(cols_id_muestra)}", "e"
        
    cols_unicas = list(cols_id_resultado)
    if len(cols_unicas) != 2:
        return False, cols_unicas,f"No hay 2 atributos ID ({', '.join(str(col) for col in cols_unicas)}). Solo se admiten tablas con 2 columnas ID, p.ej. ID_A, ID_B, en cada tabla", "e"
    
    # Lineas 80 - 89 codigo adaptado con IA
    idx_resultado = pd.MultiIndex.from_frame(df_resultado[cols_unicas].astype(str))
    idx_muestra = pd.MultiIndex.from_frame(df_muestra[cols_unicas].astype(str))
    
    # Verificar si todas las parejas de la muestra existen en el resultado
    parejas_en_resultado = idx_muestra.isin(idx_resultado)
    
    if not parejas_en_resultado.all():
        # Contamos cuántas parejas no se encontraron
        parejas_no_halladas = idx_muestra[~parejas_en_resultado]
        num_no_halladas = len(parejas_no_halladas)
        print(f"\n[ADVERTENCIA] Pares de IDs en conflicto ({cols_unicas}):")
        print(parejas_no_halladas.tolist())
        return False, cols_unicas, f"Hay {num_no_halladas} parejas de IDs en la muestra que no existen en el resultado.", "e"
    
    return True, cols_unicas, "Compatibilidad entre muestra y resultado. Validando...", None

# FUNCIONES QUE SE USAN EN validar_muestra.py
def obtener_matriz_confusion(df_resultado: pd.DataFrame, df_muestra: pd.DataFrame):
    proceder, cols_ids, msj, modo_msj = comprobar_compatibilidad_tablas(df_resultado, df_muestra)
    if not proceder:
        return  None, None, msj, modo_msj
    # para que df sea correcto y fusione la misma cantidad y no N con M, sino N con N -> INNER
    df = pd.merge(df_resultado, df_muestra, on= cols_ids, how= "inner")
    matriz_confusion = pd.crosstab(df["rcc8_muestra"], df["rcc8_resultado"], dropna=False)
    return matriz_confusion, df, msj, modo_msj
