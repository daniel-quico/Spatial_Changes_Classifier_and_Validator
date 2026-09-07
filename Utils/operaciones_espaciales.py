"""
  Este módulo se encarga de las operaciones espaciales en sí, tratamiento general de geodataframes y uso de shapely.
  
  Uso:
    Se importan las funciones requeridas de este módulo a otros scripts según necesidad  

CÓDIGO DE ELABORACIÓN PROPIA: lógica de negocio y adaptación con uso de librerías shapely, numpy y geopandas
Basado en pruebas unitarias realizadas en Colab.
"""

import numpy as np
import geopandas as gpd
import pandas as pd
import shapely
import sys, os
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Utils.imprimir_mensajes import log_message
from Config.consts import LIMITE_MIN, items_capa, dimensiones_geom
from Utils.operaciones_descriptivas import agrupar_descripciones
from Utils.calculo_umbral_EC import calcular_umbral
# Variables locales
creadores_multigeom = {0: shapely.multipoints, 1: shapely.multilinestrings, 2: shapely.multipolygons}

# Funciones
def normalizar_area(gdf: gpd.GeoDataFrame):
    """Normalización del área bajo la siguiente lógica:
    - En caso de no disponer de un atributo llamado 'Shape_Area' se crea y se calcula su área.
    - Si se dispone de un atributo de área que no coincide con el deseado, se renombra y se recalcula su área
    - En caso de disponer de 'Shape_Area' (con las mismas minúsculas y mayúsculas) se recalcula su área"""
    # Se busca cualquier columna que contenga "area" ignorando mayúsculas
    cols_area = [col_gdf for col_gdf in gdf.columns if "area" in col_gdf.lower()]

    if len(cols_area) != 0 and cols_area[0] != "Shape_Area":
        # Se toma la primera encontrada y se renombra a "area"
        gdf = gdf.rename(columns={cols_area[0]: "Shape_Area"})
    # En caso de no existir columna Shape_Area, se crea. En caso de existir se recalcula
    gdf["Shape_Area"] = gdf.geometry.area
    return gdf

def obtener_dims_originales_gc(gdf: gpd.GeoDataFrame, gdf_dims: set):
    """Obtiene las dimensiones según el tipo de GeometryCollection disponibles y se añaden al set de gdf_dims

    **Parámetros**:
        gdf (gpd.GeoDataFrame): geodataframe con elementos de tipo GeometryCollection
        gdf_dims (set): set de dimensiones base del gdf completo
    """
    dimensiones_gc = gdf.geometry.apply(
      lambda geom: tuple(set(shapely.get_dimensions(g) for g in geom.geoms))
    )
        
    dims_unicas_gc = dimensiones_gc.drop_duplicates().reset_index(drop=True)
    #print(dims_unicas_gc)
    for dims in dims_unicas_gc:
      for dim in dims:
        gdf_dims.add(int(dim))

def limpiar_gc(geom: shapely.geometry, dim_elegida:int):
    """Filtra las geometrías contenidas en un GeometryCollection que coinciden con la dimensión
    elegida por el usuario.

    **Parámetros:**
    - geom (geometry): GeometryCollection de entrada
    - dim_elegida (int): dimensión elegida por el usuario

    **Resultados:**
    - None: cuando no hay ninguna geometría cuya dimensión sea coincidente con dim_elegida
    - shapely.geometry: 1 a N geometrías coincidentes con dim_elegida dimensionalmente  
      En caso de ser 1 solo elemento el que cumpla condición se devuelve esa geometría simple.  
      En caso de ser N elementos, se crea colección Multi- de esos elementos simples.
    """
    # https://shapely.readthedocs.io/en/2.1.2/constructive.html
    # https://shapely.readthedocs.io/en/2.1.2/reference/shapely.get_parts.html#shapely.get_parts
    # Se obtienen las partes del gdf e igualmente se obtienen sus dimensiones al ser ya unidades simples es más fácil
    partes = shapely.get_parts(geom)
    dimensiones_partes = shapely.get_dimensions(partes)
    partes_filtradas = partes[dimensiones_partes == dim_elegida]
    #print(partes_filtradas)
    if len(partes_filtradas) == 0:
      return None
    return partes_filtradas[0] if len(partes_filtradas) == 1 else creadores_multigeom[dim_elegida](partes_filtradas)

def obtener_dimensiones(gdf: gpd.GeoDataFrame, dim_elegida: int):
    """Obtiene las dimensiones topológicas de una capa, se filtra para tener la capa con las condiciones
    de homogeneidad dimensional.
    
    <h2>Parámetros</h2>
      - **gdf (gpd.GeoDataFrame):** Capa vectorial a analizar  
      - **dim_elegida (int):** dimensión elegida por el usuario
    
    <h2>Resultados</h2>
      - **(None, set):** Se devuelve None y las dimensiones que hay en el gdf si no hay coincidencia dimensional con *dim_elegida*
      - **(gpd.GeoDataFrame, set):** Se devuelve un GeoDataFrame homogéneo y las dimensiones que habían en el gdf antes de homogeneizarse
    """
    tipos_geom = set(gdf.geom_type)
    #gdf_dims = list(set(shapely.get_dimensions(gdf.geometry)))
    #gdf_dims = set(shapely.get_dimensions(gdf.geometry))
    dimensiones_base = shapely.get_dimensions(gdf.geometry.values)
    gdf_dims = set(int(d) for d in dimensiones_base if not np.isnan(d))
    # [PARTE A] Se filtra para tener las geometrias simples con la dimension elegida por el usuario
    gdf_geoms_simples = gdf[gdf.geometry.geom_type != 'GeometryCollection']
    gdf_dim_elegida = gdf_geoms_simples[shapely.get_dimensions(gdf_geoms_simples.geometry) == dim_elegida].copy()
    
    gdf_gc_filtrado = gpd.GeoDataFrame(columns=gdf.columns, crs=gdf.crs)
    if 'GeometryCollection' in tipos_geom:
        # [PARTE B] Se obtiene las geometrias que son GeometryCollection para tratarlos
        gdf_gc = gdf[gdf.geometry.geom_type == 'GeometryCollection'].copy()
        obtener_dims_originales_gc(gdf_gc, gdf_dims)
        gdf_gc['geometry'] = gdf_gc.geometry.apply(lambda geom: limpiar_gc(geom, dim_elegida))
        gdf_gc_filtrado = gdf_gc[gdf_gc.geometry.notnull() & ~gdf_gc.geometry.is_empty].copy()
    if gdf_dim_elegida.empty and gdf_gc_filtrado.empty:
        return None, gdf_dims
        
    gdf_homogeneo = gpd.GeoDataFrame(
        gpd.pd.concat([gdf_dim_elegida, gdf_gc_filtrado], ignore_index=True),
        crs=gdf.crs
    )

    return gdf_homogeneo, gdf_dims

def analizar_dimensiones_capas(capas:dict, dim_elegida: int):
    """Esta función se encarga de obtener en el diccionario de entrada las capas que cumplan
    la condición de coincidir con la dimensión elegida.   
    - Si la capa no dispone de la dimensión requerida no se añade al diccionario resultante
    - Si la capa ya era homogénea se añade al diccionario de capas resultante
    - En caso de que una capa sea mixta, se filtra para obtenerla por la dimensión requerida si
      hay geometrías con esa dimensión.
      
    **Parámetros:**
        capas (dict): diccionario de entrada con clave **nombre_archivo** y valor otro diccionario dónde se encuentra el gdf
        dim_elegida (int): dimensión seleccionada por el usuario previamente
    **Resultados:**
        dict: diccionario de capas vacío o >= 2 capas.
    """
    # Se obtienen las dimensiones de cada capa y después se comparan de par en par para avisar al usuario en el caso debido
    capas_validas = {}
    set_dims_capas = set()
    #https://www.w3schools.com/python/ref_set_update.asp
    for nombre, datos in capas.items():
        gdf, dims_original = obtener_dimensiones(datos[items_capa[0]], dim_elegida)
        set_dims_capas.update(dims_original)
        dims = list(dims_original)
        if gdf is None:
            log_message(f"Las dimensiones de la capa '{nombre}' no coincide con la dimensión elegida ({dim_elegida}).", "e")
            log_message("Descartando capa...", None)
            log_message(f"Capa '{nombre}' descartada con éxito", "1")
            # No se añade al nuevo diccionario
            continue
        
        if len(dims) > 1:
            log_message(f"La capa '{nombre}' era un conjunto de datos mixto {tuple(dims_original)}. Para usar esta herramienta es necesario mantener una homogeneidad dimensional.", "a")
            log_message("Filtrando capa...", None)
            log_message(f"Capa '{nombre}' filtrada correctamente por dimensión {dim_elegida}", "1")
        
        else:
          tipo_elementos = dimensiones_geom[dim_elegida]+"es" if dim_elegida != 2 else "de " + dimensiones_geom[dim_elegida]
          log_message(f"El conjunto de datos en la capa '{nombre}' es homogéneo dimensionalmente. Dimensión {dims[0]}: Elementos {tipo_elementos}", "1")
        capas_validas[nombre] = {
            items_capa[0]: gdf,
            items_capa[1]: datos[items_capa[1]],
            items_capa[2]: datos[items_capa[2]]
        }
    if len(capas_validas) < LIMITE_MIN:
        log_message(f"No hay capas suficientes que tengan dimensión {dim_elegida}. Mínimo tiene que haber {LIMITE_MIN} capas válidas para poder procesar", "e")
        return {}
    print()
    if len(list(set_dims_capas)) > 1:
        log_message(f"Dimensiones globales detectadas inicialmente en el conjunto: {list(set_dims_capas)}", "1")
        log_message(f"Se ha homogeneizado el proyecto. Ahora se trabaja con un conjunto de {len(capas_validas)} capas válidas {tipo_elementos}", "o")    
    else:
        log_message(f"El conjunto de capas proporcionado es homogéneo. Elementos {tipo_elementos}", "o")
    print()
    return capas_validas

def tratar_capas(capa: gpd.GeoDataFrame, num_orden: str):
    """Evalúa si la capa tiene el atributo de interés renombrado a **ID**:
    - En caso de que lo tenga se separan los nulos de los no nulos. De tal manera que si
    hay nulos se modificará su valor a '[num_orden]_id_desconocido_[num_asociado]'. Para después obtener
    una tabla concatenada entre los valores con los no nulos disueltos por su atributo y los
    nulos modificados
    - En caso de no disponer del atributo de interés, se obtiene la capa con un atributo **ID** tal que
    así 'geom_[indice_fila]'
    
    Parámetros:
    - capa (gpd.GeoDataFrame): capa de entrada a evaluar
    - num_orden (str): identificador numérico de la capa
    
    Resultados (gpd.GeoDataFrame, bool):
    - Opción 1 (misma_capa, False): si no existe el atributo de interés se devuelve con un "ID" asociado a su índice de la tabla
    - Opción 2 (capa_tratada, True): si existe el atributo de interés, se tratarán los nulos para ese atributo (si hay).
    """
    if "ID" not in capa.columns:
        capa["ID"] = "geom_" + capa.index.to_series().astype(str)
        return normalizar_area(capa), False
    gdf_con_id = capa[capa["ID"].notna()]
    gdf_sin_id = capa[capa["ID"].isna()]
    if not gdf_sin_id.empty:
        gdf_sin_id["ID"] = gdf_sin_id["ID"].fillna(num_orden +"_id_desconocido_" + gdf_sin_id.index.to_series().astype(str))

    if gdf_con_id["ID"].duplicated().any():
        gdf_con_id = capa.dissolve(by="ID", dropna=True).reset_index()
    return normalizar_area(gpd.GeoDataFrame(pd.concat([gdf_con_id, gdf_sin_id], ignore_index=True), crs=capa.crs)), True

def descartar_comparacion(gdf_A: gpd.GeoDataFrame, gdf_B: gpd.GeoDataFrame) -> bool:
    """Función que devuelve un valor para descartar o no la comparación entre par de capas.

    Parámetros:
        gdf_A (gpd.GeoDataFrame): El geodataframe i
        gdf_B (gpd.GeoDataFrame): El geodataframe i+1

    Resultado:
        bool: True / False
    """
    # https://shapely.readthedocs.io/en/2.1.2/reference/shapely.box.html
    bbox_A = shapely.box(*gdf_A.total_bounds)
    bbox_B = shapely.box(*gdf_B.total_bounds)
    if not bbox_A.intersects(bbox_B):
        return True
    intersecciones = gdf_B.sindex.query(gdf_A.geometry, predicate="intersects")
    return intersecciones[1].size == 0
    # https://www.geeksforgeeks.org/numpy/numpy-where-in-python/ np.where

def calcular_coeficientes(sub_gdf_con_relacion: gpd.GeoDataFrame, gdf_A: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Calcula los coeficientes de los elementos relacionados entre A y B que no sean DC

    **Parámetros:**
        sub_gdf_con_relacion (gpd.GeoDataFrame): subtabla de aquellos elementos que sí intersecan
        gdf_A (gpd.GeoDataFrame): tabla A original
    **Resultados:**
        gpd.GeoDataFrame: tabla con los coeficientes correspondientes calculados
    """
    idx_A = sub_gdf_con_relacion["index_A"].astype(int).values
    geom_A = gpd.GeoSeries(gdf_A.loc[idx_A]["geometry"].values, index=sub_gdf_con_relacion.index)
    area_A = gdf_A.loc[idx_A]["Shape_Area"].values
    
    geom_B = sub_gdf_con_relacion["geometry"]
    area_B = sub_gdf_con_relacion["Shape_Area_B"]
    
    interseccion = geom_B.intersection(geom_A).area
    union = geom_B.union(geom_A).area
    
    sub_gdf_con_relacion["coef_igualdad"] = interseccion / np.where(union > 0, union, 1)
    sub_gdf_con_relacion["coef_contain"] = interseccion / np.where(area_A > 0, area_A, 1)
    sub_gdf_con_relacion["coef_within"] = interseccion / np.where(area_B > 0, area_B, 1)
    sub_gdf_con_relacion["coef_interseccion"] = np.maximum(sub_gdf_con_relacion["coef_within"], sub_gdf_con_relacion["coef_contain"])    
    return sub_gdf_con_relacion
    
def asignar_relacion_rcc8(sub_gdf_con_relacion: gpd.GeoDataFrame, gdf_A:gpd.GeoDataFrame, anios: list, umbrales: dict, id_disponible: bool) -> gpd.GeoDataFrame:
    """Crea dos columnas nuevas en la tabla de entrada y asigna descripciones según la casuística
    del tipo de relación que tenga bajo su respectiva condición con su umbral

    **Parámetros:**
        sub_gdf_con_relacion (gpd.GeoDataFrame): subtabla de entrada
        gdf_A (gpd.GeoDataFrame): tabla A original
        anios (list): lista de par de años o num_orden correspondientes al par de capas
        umbrales (dict): diccionario de umbrales del usuario
        id_disponible (bool): True/False según si había atributo de interés o no en cada capa

    **Resultado**:
        gpd.GeoDataFrame: subtabla con sus rcc8 diferentes a DC
    """
    if id_disponible:
        es_mismo_id = sub_gdf_con_relacion["ID_B"] == sub_gdf_con_relacion["ID_A"]
        ids_existentes_A = set(gdf_A['ID'].dropna().astype(str).unique())
        es_id_nuevo = ~sub_gdf_con_relacion['ID_B'].isin(ids_existentes_A) & ~sub_gdf_con_relacion['ID_B'].str.startswith(f"{anios[1]}")
    else:
        es_mismo_id = pd.Series(False, index=sub_gdf_con_relacion.index)
        es_id_nuevo = pd.Series(False, index=sub_gdf_con_relacion.index)
    # Para quitar las colindacncias puras entre IDs diferentes tal que no sean IDs_nuevos
    coef_interseccion = sub_gdf_con_relacion['coef_interseccion']
    umbral_ec = calcular_umbral(sub_gdf_con_relacion[coef_interseccion < umbrales['interseccion']]) if umbrales["interseccion"] != 0  else 0
    es_colindante_puro = coef_interseccion <= umbral_ec  #0.000001 #0.00000001
    #filas_a_quitar =  es_colindante_puro & (~es_mismo_id) & (~es_id_nuevo)
    #sub_gdf_con_relacion = sub_gdf_con_relacion[~filas_a_quitar].copy()
    # Debido a esto hay que reindexar
    #es_mismo_id = es_mismo_id.loc[sub_gdf_con_relacion.index]
    #es_id_nuevo = es_id_nuevo.loc[sub_gdf_con_relacion.index]
    
    # CONDICIONES Y CLASIFICACIÓN SEGÚN EL UMBRAL
    condiciones = [
        # EQ: Igualdad espacial
        (sub_gdf_con_relacion['coef_igualdad'] >= umbrales['igualdad']) & es_mismo_id,  # EVOLUTIVO: Comparar con los vecinos que intersecan con la misma geom_A para cada EQ_2 si ha habido una relación diferente a un PO bajo, a otro EQ y a EC en sus vecinos, para ya no evaluar el IoU, sino los otros coeficientes
        (sub_gdf_con_relacion['coef_igualdad'] >= umbrales['igualdad']) & (~es_mismo_id),
        # TPP/NTPP: Fusión / A Contenido en B
        (sub_gdf_con_relacion['coef_contain'] >= umbrales['contain']) & (sub_gdf_con_relacion['coef_contain'] > sub_gdf_con_relacion['coef_within']),
        # TPPi/NTPPi: Segregación / A Contiene a B
        (sub_gdf_con_relacion['coef_within'] >= umbrales['within']) & (sub_gdf_con_relacion['coef_within'] > sub_gdf_con_relacion['coef_contain']),
        # PO: Solape parcial significativo
        sub_gdf_con_relacion['coef_interseccion'] >= umbrales['interseccion'],
        # EC: Colindancia entre A y B siendo de mismo ID (esto es muy raro que pase) 
        es_mismo_id,
        # EC: Colindancia entre A y B con diferente ID y con posibles variaciones en la digitalazicación entre ambas capas
        (~es_mismo_id) & (~es_colindante_puro)
    ]
    parcial_total_EQ = " (totalmente si no hay error topográfico. Parcialmente si hay algún error topográfico)"
    descripciones = [
        f"EQ_2: Misma geometría y mismo ID{parcial_total_EQ if umbrales['igualdad'] < 0.95 else ""}",
        f"EQ_1: Misma geometría{", diferente ID" if id_disponible else ""}{parcial_total_EQ if umbrales['igualdad'] < 0.95 else ""}",
        f"TPPi/NTPPi: Entidad de capa_{anios[0]} contenida por entidad de capa_{anios[1]} / Fusión",
        f"TPP/NTPP: Entidad de capa_{anios[0]} contiene a entidad de capa_{anios[1]} / Segregación",
        "PO: Solape parcial / Mutación de límites",
        f"EC_1: Colindancia entre capas con el mismo ID (puro o con solapamiento menor al {umbrales['interseccion']*100}%)",
        "EC_2: Colindante por error/corrección topográfico/a"
    ]
    # Mapeo según las condiciones con np.select: https://www.geeksforgeeks.org/python/numpy-select-function-python/
    desc_base = np.select(condiciones, descripciones, default="EC_2: Colindante puro")
    sub_gdf_con_relacion["relacion"] = np.where(es_id_nuevo, desc_base + f". ID_{anios[1]} es nuevo", desc_base)
    sub_gdf_con_relacion["estado"] = np.where(sub_gdf_con_relacion["relacion"].str.startswith("EQ"), "fijo", "cambio")
    
    return sub_gdf_con_relacion
    
def tratamiento_dc(gdf_tipo_DC: gpd.GeoDataFrame, ids_capa_contraria: list, cols_id: list, msj_adicional: str, id_disponible: bool):
    col_id, ids_gdf = cols_id
    descripcion_dc = "DC: Sin relación espacial con entidades de la capa anterior"
    if not id_disponible:
        gdf_tipo_DC[col_id] = None
        gdf_tipo_DC['relacion'] = f"{descripcion_dc} {msj_adicional}"
    
    else:
        pertenece = gdf_tipo_DC[ids_gdf].isin(ids_capa_contraria)
        gdf_tipo_DC[col_id] = np.where(pertenece, gdf_tipo_DC[ids_gdf], "")
        gdf_tipo_DC['relacion'] = np.where(pertenece, descripcion_dc, f"{descripcion_dc} {msj_adicional}")
        
def comparar_capas_pares(gdf_A: gpd.GeoDataFrame, gdf_B: gpd.GeoDataFrame, anios: list, umbrales: dict, pbar: tqdm, id_disponible: bool, dim: int):
    """Compara dos capas y devuelve las tablas en gdf, df_fijos, df_cambio y reporte (resumen de los resultados de gdf agrupados)"""
    col_id_A = f"ID_{anios[0]}"
    col_id_B = f"ID_{anios[1]}"
    
    # Se realiza la INTERSECCIÓN entre geometrías de A con cada geometría de B
    intersecciones = gdf_B.sjoin(gdf_A, how="left", predicate="intersects", lsuffix="B", rsuffix="A").reset_index()
    pbar.update(1)
    
    tiene_relacion = intersecciones["index_A"].notna()
    # Se procesan los elementos CON RELACIÓN: RCC8 DE B-A
    sub_gdf_con_relacion = calcular_coeficientes(intersecciones[tiene_relacion].copy(), gdf_A)
    pbar.update(1)
    sub_gdf_con_relacion_rcc8 = asignar_relacion_rcc8(sub_gdf_con_relacion, gdf_A, anios, umbrales, id_disponible)
    sub_gdf_con_relacion_rcc8[col_id_A] = sub_gdf_con_relacion_rcc8["ID_A"]
    sub_gdf_con_relacion_rcc8[col_id_B] = sub_gdf_con_relacion_rcc8["ID_B"]
    
    # Se procesan los elementos SIN RELACIÓN (DC): NUEVOS DE B
    sub_gdf_sin_relacion_rcc8 = intersecciones[~tiene_relacion].copy()
    #tqdm.write(sub_gdf_con_relacion_rcc8.head(5))
    tratamiento_dc(sub_gdf_sin_relacion_rcc8, gdf_A["ID"].to_list(), [col_id_A, "ID_A"], f"({col_id_B} es nuevo)", id_disponible)
    #sub_gdf_sin_relacion_rcc8[col_id_A] = None  # afecta aqui
    sub_gdf_sin_relacion_rcc8[col_id_B] = sub_gdf_sin_relacion_rcc8["ID_B"]
    for tipo in umbrales.keys():
        sub_gdf_sin_relacion_rcc8[f"coef_{tipo}"] = np.nan
    #sub_gdf_sin_relacion_rcc8['relacion'] = f"DC: Sin relación espacial con entidades de la capa anterior ({col_id_B} es nuevo)"    # afecta aqui
    sub_gdf_sin_relacion_rcc8["estado"] = "cambio"
    
    # Se procesan los elementos SIN RELACIÓN (DC): PERDIDOS A
    idx_A_relacionados = intersecciones[tiene_relacion]["index_A"].unique()
    indices_perdidos_A = gdf_A.index.difference(idx_A_relacionados)
    if len(indices_perdidos_A) > 0:
        # https://www.datacamp.com/tutorial/loc-vs-iloc?utm_cid=19589720821&utm_aid=157156374671&utm_campaign=230119_1-ps-other~dsa-tofu~all_2-b2c_3-emea_4-prc_5-na_6-na_7-le_8-pdsh-go_9-nb-e_10-na_11-na&utm_loc=9061050-&utm_mtd=-c&utm_kw=&utm_source=google&utm_medium=paid_search&utm_content=ps-other~emea-en~dsa~tofu~tutorial~data-science&gad_source=1&gad_campaignid=19589720821&gbraid=0AAAAADQ9WsHoulchSqiDhHdjxY1HtXF2o&gclid=Cj0KCQjwhsrUBhDxARIsAN3AQSe-CnCoM9mA4xBGgazbxyn_yobpWa32h2x27AFZ61D2JPruGMu7tHEaAi4MEALw_wcB
        gdf_A_perdidos = gdf_A.loc[indices_perdidos_A].copy()
        gdf_A_perdidos[col_id_A] = gdf_A_perdidos["ID"]
        tratamiento_dc(gdf_A_perdidos, gdf_B["ID"].to_list(), [col_id_B, "ID_B"], f"({col_id_A} se ha perdido)", id_disponible)
        #gdf_A_perdidos[col_id_B] = None # afecta aqui
        for tipo in umbrales.keys():
            gdf_A_perdidos[f"coef_{tipo}"] = np.nan
        #gdf_A_perdidos['relacion'] = f"DC: Sin relación espacial con entidades de la capa siguiente ({col_id_A} se perdió)" # afecta aqui
        gdf_A_perdidos['estado'] = "cambio"
    
    pbar.update(1)
    
    # CONCATENACIÓN FINAL de los DC con los RELACIONADOS y OBTENCIÓN de RESULTADOS
    df_rcc8 = pd.concat([sub_gdf_con_relacion_rcc8, sub_gdf_sin_relacion_rcc8], ignore_index=True)
    
    cols_df_secundarios = [col_id_B, col_id_A, 'coef_igualdad', 'coef_interseccion', 'coef_within', 'coef_contain', 'relacion']
    df_secundario_fijos = df_rcc8[df_rcc8['estado'] == 'fijo'][cols_df_secundarios]    
    df_secundario_cambios = df_rcc8[df_rcc8['estado'] == 'cambio'][cols_df_secundarios]
    
    gdf_rcc8 = gpd.GeoDataFrame(df_rcc8, geometry="geometry", crs=gdf_B.crs)
    # https://medium.com/@heyamit10/understanding-groupby-and-aggregate-in-pandas-f45e524538b9
    gdf_agrupado = gdf_rcc8.groupby(col_id_B).agg({
        col_id_A: lambda id_A: ", ".join(sorted(list(id_A.dropna().astype(str)))),
        "estado": "first",
        "relacion": lambda descripcion: agrupar_descripciones(descripcion, id_disponible),
        "geometry": "first"
    }).reset_index()
    
    gdf_principal = gpd.GeoDataFrame(gdf_agrupado, geometry="geometry", crs=gdf_B.crs)
    cols_gdf_principal = [col_id_B, col_id_A, "estado", "relacion", "geometry"]
    
    # En caso de que se hayan perdido elementos de gdf_A
    if len(indices_perdidos_A) > 0:
        df_secundario_cambios = pd.concat([df_secundario_cambios, gdf_A_perdidos[cols_df_secundarios]], ignore_index=True)    
        gdf_principal = gpd.GeoDataFrame(pd.concat([gdf_principal, gdf_A_perdidos[cols_gdf_principal]], ignore_index=True), geometry="geometry", crs=gdf_B.crs)
    
    resumen_tipos = gdf_principal.groupby('relacion').size().reset_index(name='TOTAL')
    pbar.update(1)
    return gdf_principal, df_secundario_fijos, df_secundario_cambios, resumen_tipos