# Spatial_Changes_Classifier_and_Validator
## Trabajo Fin De Titulación
**Autor:** Daniel Antonio Quico Cuya  
**Tutor:** Luis Manuel Vilches Blázquez  
**Titulación:** Grado en Ingeniería de las Tecnologías de la Información Geoespacial.  
**Institución:** Universidad Politécnica de Madrid (UPM)  
**Centro:** Escuela Técnica Superior de Ingenieros en Topografía, Geodesia y Cartografía (ETSITGC)  
<img src="https://www.upm.es/gsfs/SFS24540" alt="Escudo UPM" width="230">
<img src="https://www.upm.es/gsfs/SFS12102" alt="Escudo ETSITGC" width="300">

----------------------------------------------------
> Recomendado leer este fichero ya que describe la arquitectura y ofrece indicaciones sobre el uso de la herramienta y el código para llevar a cabo este proyecto.
## Descripción
Este proyecto consiste en el desarrollo de una herramienta Python que trata con capas vectoriales homogéneas (u homogeneizadas en la ejecución) con el fin de poder clasificar relaciones 
entre pares de capas mediante cálculos por su respectiva unidad de medida y validarlo, ofreciendo el usuario una muestra, con respecto a los resultados correspondientes.

## Tabla de Contenido
- [Requisitos previos](#requisitos-previos)
- [Arquitectura](#arquitectura)
- [Scripts](#scripts)
- [Resultados](#resultados)
- [Fuentes de inspiración y de apoyo](#fuentes-de-datos)
- [Licencia](#licencia)

## Requisitos previos
En caso de trabajar en local, es decir en un editor de texto como Visual Studio Code se recomienda realizar los siguientes pasos (si no tiene un intérprete que pueda descargar las librerías):
- Descargar MiniConda en https://continuumio-docs.readthedocs-hosted.com/miniconda/install/.
- Ir a la seccion de Installing MiniConda y según el S.O descargar la versión de interés del usuario (para la realización de este proyecto se ha usado la versión conda 26.5.3).
- Configurar miniconda por defecto, excepto el lugar de donde quieras descargarlo y abrir Anaconda Prompt

Una vez con el prompt abierto (en caso de no disponer de una variable de entorno) se crea una variable de entorno nueva y vacía. Posteriormente se activa si se desea usar la herramienta.
```
conda create -n spatial_env
conda activate spatial_env
```
A continuación, se instalan las librerías necesarias.
```
conda install python
conda install -c conda-forge geopandas
conda install conda-forge::gdal
conda install conda-forge::inquirerpy
conda install conda-forge::tqdm
conda install pathvalidate
```
Y finalmente en Visual Studio Code se realizan las siguientes acciones para poder establecer tu variable de entorno como intérprete en la ejecución de los procesos:
1. **CTRL + SHIFT + P**
2. **Python: Select Interpreter**
3. **Busca el intérprete (archivo python.exe) de spatial_env**: C:\Usarios\{TU_USUARIO}\miniconda3\envs\spatial_env

## Arquitectura
Este repositorio viene con la siguiente estructura.
```
Spatial_Changes_Classifier_and_Validator/
├── capas/
├── Config/
│   └── consts.py
├── muestras/
├── Procesos/
│   ├── comparacion.py
│   └── validacion.py
├── resultados_clasificacion/
├── resultados_validacion/  
├── Utils/
│   ├── calculo_tiempo.py
│   ├── calculo_umbral_EC.py
│   ├── comparacion_capas.py
│   ├── descargar_resultados.py
│   ├── herramientas_ui.py
│   ├── imprimir_mensajes.py
│   ├── lectura_formato.py
│   ├── leer_archivos_csv.py
│   ├── leer_capas.py
│   ├── operaciones_descriptivas.py
│   ├── operaciones_espaciales.py
│   └── validar_muestra
└── README.md
```
## Scripts y Carpetas
### Config/consts.py
Contiene variables que se guardan como constantes para tratar con ellos de manera dinámica o en varios scripts.

### capas/
Carpeta dónde se guardan las capas de información, específicamente en esta herramienta se admiten los formatos GEOJSON, SHP y GPKG. Las capas a escanear (y si cumple con las configuraciones, a comparar)
tienen que subirse a esta carpeta sin estar contenidas por otras subcarpetas.
### Procesos/comparacion.py
Script **ejecutable** para correr el programa de comparación. Dándose en primer lugar el escaneo de capas, la configuración de comparación y luego el cálculo los ratios de la unidad de medida para la clasificación de relaciones
espaciales bajo los umbrales dados por el usuario.
### resultados_clasificacion/
Carpeta dónde se exportan los resultados de cada par de comparaciones, creándose para cada vez que se ejecuta el proceso de comparación un archivo .txt con los umbrales usados en esa ejecución.
Como también, 1-N subcarpetas con el nombre establecido en la ejecución, la cual contiene archivos CSV: de fijos, cambios y total de ambas; estadísticas de cada relación y reporte agrupado.
Como de un archivo GPKG que contiene las geometrías del valor a predecir clasificación con sus 1-M relaciones asociadas concatenadas en el atributo "relacion".


### muestras/
Aquí se recomienda tener las muestras, obligatorio que sea en formato CSV, con 3 columnas: "ID_[B]", "ID[A]", "relacion", siendo [B] y [A] los mismos subíndices que los generados en los resultados.
Como también se recomienda que cada fichero de muestra se llame "muestra_[NOMBRE]_[A]_[B].csv" para poder tener una mejor organización en esta carpeta.
### Procesos/validacion.py
Script **ejecutable** para correr el programa de validación. Iniciando con la lectura de archivos CSV y mostrando al usuario que par muestra-resultado quiere validar de los disponibles.Dando como resultado 
una matriz de confusión y unas métricas de evaluación de la clasificación (este último informe se muestra en pantalla).
### resultados_validacion/
Carpeta dónde se exportan las matrices de confusión de la validación entre muestras y resultados (REAL-PREDICHO).

### Utils/
Carpeta que contiene los módulos de Python que encapsulan la lógica de negocio y funciones de soporte (lectura de E/S, filtrado, operaciones espaciales, etc.), de tal manera que cada script
tenga un conjunto de tareas a realizar o funcionar de helpers.
#### Utils/leer_capas.py
Módulo que escanea el *dataset* de la carpeta *capas/*.
- Se apoya en las funciones *leer_formatos* y *establecer_epsg_tratamiento* del módulo ***lectura_formato.py*** para tratar con el EPSG definido por el usuario, obteniendo el conjunto de 
capas que tengan un SRC (Sistema de Referencia de Coordenadas) asociado tratado.  
- Resultando de N<=M capas, siendo N el número válido de capas y M el tamaño del *dataset* original. Si no hay mínimo 2 capas válidas, se interrumpe la ejecución con mensaje de error.
- En caso de que se supere esa cantidad mínima de capas, se elige con qué dimensión espacial trabajar, como con la configuración del orden del conjunto de capas 
y un filtro para la obtención de capas homogéneas dimensionalmente. 
Si nuevamente no se supera el mínimo de capas válidas, se interrumpe la ejecución con mensaje de error en pantalla.
- En caso contrario se evalúa si la herramienta tendrá una clasificación tomando en cuenta un atributo en común en el *dataset* válido,
o si será puramente geométrico (geometría a geometría) al no haber un atributo en común. 
- O si el usuario hubiese querido interrumpir la ejecución en esta última parte, puede hacerlo para realizar un estudio de sus datos o preprocesamiento si lo considera oportuno. 
En caso de que hayan mínimo 2 capas válidas con las condiciones del flujo: Devuelve un diccionario {"[nombre_capa]":{"gdf":gpd.GeoDataFrame,"num_orden":int, "año": -1 | int | None}} y la dimensión de tratamiento.
#### Utils/leer_archivos_csv.py
Módulo que se encarga de:
- escanear archivos CSV que se ubican en las carpetas de resultados correspondientes. Se apoya en la función *leer_formatos* de ***lectura_formato.py*** para leer los ficheros como 
DataFrame.
- Después se trata con cada tabla para obtener cuantos CSVs fueron válidos en la lectura. En caso de no disponer de mínimo uno de los dos ficheros (CSV de muestra o de resultado) se interrumpe el programa.  
- Dado el caso de éxito, se muestra al usuario cuál de los archivos disponibles para cada tipo (muestra y resultado) quiere usar para la validación.
En caso de que el flujo no haya sido interrumpido por errores, se devuelven la muestra elegida y el resultado elegido como diccionarios ambos en formato {"nombre":str, "df":pd.DataFrame}
#### Utils/lectura_formato.py
Módulo de apoyo que puede tratar con el formato del input escaneado, como de tratar con un EPSG válido.  
- La primera función mencionada ofrece lo dicho con anterioridad, cuyo deber principal es leer como tabla de datos (GeoDataFrame o DataFrame) cada archivo.  
- La segunda función mencionada ofrece una interacción del usuario de escoger un EPSG de tratamiento que sea proyectado mediante un bucle y solicitud por teclado.
En el caso de tratar con un GeoDataFrame puede establecer, cambiar de CRS al elegido por el usuario y devolver la tabla procesada.

#### Utils/comparacion_capas.py
Este módulo sigue los siguientes pasos:
- Establecimiento de umbrales (thresholds), apoyándose en ***herramientas_ui.py*** para los coeficientes de igualdad, within, contain e intersección (por el momento, un nuevo desarrollo añadirá nuevos umbrales para extender la herramienta a elementos lineales, dimensión 1).
- Solicitud de un nombre válido para los archivos y subcarpetas a generar en ***resultados_clasificacion/***. Apoyándose en ***herramientas_ui.py***.
- Tratamiento de las capas disponibles según la configuración realizada en ***leer_capas.py***. Se apoya en ***operaciones_espaciales.py***.
- Normalización de la medida que servirá para el cálculo de los coeficientes. En caso de ser una comparación puramente geométrica se generan IDs automáticos para poder identificar cómo se relaciona cada geometría. Se apoya en ***operaciones_espaciales.py***.

Una vez normalizados, se procede a iterar el *dataset* en un bucle analizando i con i+1, i+1 con i+2,... N-2 con N-1, N-1 con N 
- Evalúa si se descarta la comparación. Si no hay relación alguna entre las entidades de las capas (DC), se salta esta comparación y se avisa que no hay relación por mensaje en la terminal
- Si existen relaciones se comparan las capas y se obtienen 2 tablas descriptivas (cambios y fijos), 2 tablas del comportamiento de la clasificación (reporte agrupado de las clases concatenadas y estadísticos por clases con sus coeficientes) y una capa vectorial Geopackage.
- Descarga de los archivos mencionados si hubieron capas con relaciones. En caso de que ninguna tuviese relación con otra, N-1 mensajes de error en pantalla.
#### Utils/validar_muestra.py
Este módulo sigue los siguientes pasos:
- Solicitud de un nombre válido para la generación de un archivo CSV, correspondiente a una matriz de confusión. Apoyándose en ***herramientas_ui.py***.
- Comprobación de compatibilidad entre tablas muestra y resultado. Manejando los posibles errores al imprimirlos en pantalla e interrumpir el proceso si hay incompatibilidad.
- Obtención de una tabla cruzada y matriz de confusión. En caso de que si haya compatibilidad y la muestra sea un subconjunto del resultado. En este paso y el anterior se apoya en ***operaciones_descriptivas.py***
- Impresión en pantalla de las métricas de evaluación de la clasificación y descarga de la matriz de confusión
#### Utils/operaciones_espaciales.py
Módulo dónde se encuentra la lógica de negocio principalmente espacial que se usa como *helper* en otros scripts.
- Tratamiento de las dimensiones de una capa con la finalidad de obtener una capa homogénea y/o que cumpla con la dimensión deseada por el usuario: *obtener_dims_originales_gc*, *limpiar_gc*, *obtener_dimensiones*, *analizar_dimensiones_capas*
- Normalización de la unidad de medida para la clasificación: *normalizar_area* (próximamente normalizar_medida para tomar en cuenta los elementos lineales, ya que será con la longitud)
- Tratamiento de las capas. Si tiene un atributo identificador, se tratan nulos del atributo y se disuelve por él en caso de existir duplicados. Si no dispone de ese atributo: creación de identificadores pero comparación puramente geométrica: *trata_capas*
- Descartar comparación si no hay relación alguna entre capas: *descartar_comparacion*
- Comparación y clasificación mediante el cálculo por ratios de la unidad de medida (llamados coeficientes en este proyecto) con respecto a sus umbrales y existencia o inexistencia de atributo de interés: *calcular_coeficientes*, *asignar_relacion_rcc8*, *tratamiento_dc*, *comparar_capas*
#### Utils/calculo_umbral_EC.py
Módulo de cálculo del umbral para EC, debido a que por lógica hay muchos datos colindantes y que son la mayoría muy próximos a 0. Basándose en el rango intercuartílico. Para poder separar EC posiblemente puros del resto.
#### Utils/operaciones_descriptivas.py
Módulo dónde se encuentra la lógica de negocio principalmente descriptiva que se usa como *helper* en otros scripts.
- Verificación de que existe el atributo de interés dado por el usuario en el *dataset* completo. Y en caso de ser así se renombra a "ID": *verificar_atributo_comun* y *renombrar_atributo_interes*.
- Agrupación de descripciones por tipo de relación para generar la capa de relaciones de cada geometría 1-N: *agrupar_descripciones*, *ordenar_por_tipo*
- Analiza la compatibilidad entre tabla de Muestra y Resultado y devuelve una Matriz de Confusión si no hay errores: *comprobar_compatibilidad_tablas* y *obtener_matriz_confusion*
#### Utils/herramientas_ui.py
Módulo para interacciones con el usuario en su configuración:
- pedir_confirmacion(msj): muestra un mensaje y espera una respuesta para procesar un retorno booleano
- escoger_dimension(): muestra al usuario opciones a elegir de dimensión
- escoger_archivo(archivos, msj): muestras al usuario opciones a elegir de un archivo
- seleccionar_orden_capas(capas, nombres_archivos, opcion): muestra un listado de nombres de las capas a ordenar, con ENTER se selecciona la capa en la posición i. En la primera iteración se puede CANCELAR. Y según el método de orden se puede añadir un año o se calcula el orden por defecto de aparición, o únicamente por selección.
- gestionar_capas_sin_atr_interes(): Manejo del flujo para decidir entre si continuar y comparar geometría a geometrías las capas del *dataset*, o INTERRUMPIR la ejecución del programa.
- establecer_umbral(msj, minimo, maximo): Manejo de los umbrales solicitados al usuario por teclado.
- obtener_nombre_valido(msj): manejo de la obtención de un nombre válido en tu sistema operativo
#### Utils/imprimir_mensajes.py
Módulo para imprimir mensajes en la terminal de ejecución.
#### Utils/descargar_resultados.py
Módulo que ofrece funciones para descargar cada fichero o informe necesario en cada proceso. Tratando la escritura de los datos a exportar para que tenga una lectura correcta y segura por el usuario.
#### Utils/calculo_tiempo.py
Módulo que calcula el tiempo transcurrido desde llamada de la función:
- *comparar_capas* del módulo ***comparacion_capas.py*** si se usa el proceso ***comparacion.py***
- *validar_clasificacion* del módulo ***validar_muestra.py*** si se usa el proceso ***validacion.py***

hasta que finalice dicha función.

## Fuentes de inspiración y de apoyo
- **IoU-Calculator de Reut Keller:** https://github.com/reutkeller/iou-calculator  
- **Bounding Box (en vez de realizar un dissolve que es más costoso):** https://shapely.readthedocs.io/en/2.1.2/reference/shapely.box.html
- **Apply function (para ejecutar sobre pd.Series. O Geoseries para las dimensiones en este caso)**: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.apply.html
- **GDAL WARNING when importing geopandas:** https://gis.stackexchange.com/questions/478160/gdal-warning-when-importing-geopandas  
- **Driver GPKG:** https://gdal.org/en/stable/drivers/vector/gpkg.html  
- **Pandas Index Name:** https://pandas.pydata.org/docs/reference/api/pandas.Index.name.html  
- **PathValidate:** https://www.tradingcode.net/python/validate-check-filename/?__cf_chl_tk=rl.IP1ypWkKryO8sUzZP.OtqlwaSpJH55pFCUV.6c8Y-1783949410-1.0.1.1-MQclKEW5ph4O.YqBHHOoziZdv5w1.xeQKLva52N9W1g
- **CRS pyproj 3.7.2 documentation:** https://py.geocompx.org/06-reproj y https://pyproj4.github.io/pyproj/stable/api/crs/crs.html
- **os.walk() in Python:** https://www.geeksforgeeks.org/python/os-walk-python/
- **Datatype Introspection with pandas:** https://pandas.pydata.org/docs/reference/arrays.html#data-type-introspection
- **Ref_func_sorted (para orednar con pesos la descripción):** https://www.w3schools.com/python/ref_func_sorted.asp
- **Shapely documents (para tratar con Geometry Collections):** https://shapely.readthedocs.io/en/2.1.2/constructive.html y https://shapely.readthedocs.io/en/2.1.2/reference/shapely.get_parts.html#shapely.get_parts
- **Update Sets, W3Schools (para tratar con las dimensiones existentes en el dataset):** https://www.w3schools.com/python/ref_set_update.asp
- **Numpy use of np.where and np.select, Geeks for Geeks (para condiciones y su mapeo):** https://www.geeksforgeeks.org/numpy/numpy-where-in-python/np.where y https://www.geeksforgeeks.org/python/numpy-select-function-python/
- **Use of loc and ilocs, Datacamp:** https://www.datacamp.com/tutorial/loc-vs-iloc?utm_cid=19589720821&utm_aid=157156374671&utm_campaign=230119_1-ps-other~dsa-tofu~all_2-b2c_3-emea_4-prc_5-na_6-na_7-le_8-pdsh-go_9-nb-e_10-na_11-na&utm_loc=9061050-&utm_mtd=-c&utm_kw=&utm_source=google&utm_medium=paid_search&utm_content=ps-other~emea-en~dsa~tofu~tutorial~data-science&gad_source=1&gad_campaignid=19589720821&gbraid=0AAAAADQ9WsHoulchSqiDhHdjxY1HtXF2o&gclid=Cj0KCQjwhsrUBhDxARIsAN3AQSe-CnCoM9mA4xBGgazbxyn_yobpWa32h2x27AFZ61D2JPruGMu7tHEaAi4MEALw_wcB
- **Use of groupby with aggregate in Pandas:** https://medium.com/@heyamit10/understanding-groupby-and-aggregate-in-pandas-f45e524538b9
- **Pandas crosstab function, de Geek for Geeks:** https://www.geeksforgeeks.org/python/pandas-crosstab-function-in-python/
- **Scikit Learn (para obtener las métricas de clasificación):** https://scikit-learn.org/stable/modules/model_evaluation.html#classification-metrics y https://scikit-learn.org/stable/modules/generated/sklearn.metrics.classification_report.html
- **"El algoritmo de similitud de superposición (para el coef_interseccion y coef_within y coef_contain por lógica):** https://www.dominiovirtual.es/ordenadores-portatiles/14977/90nb0jc2-m01300/portatil-asus-zenbook-flip-13-ux362fa-el076t.html
- **El Rango Intercuartílico (para los datos atípicos, en este caso EC por defecto):** https://docs.oracle.com/cloud/help/es/pbcs_common/PFUSU/insights_metrics_IQR.htm#PFUSU-GUID-CF37CAEA-730B-4346-801E-64612719FF6B
## Licencia
Licencia bajo **GNU GPL v2.**
