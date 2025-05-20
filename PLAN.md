* Importar datos desde .csv, Excel o ingreso manual (con modal con scroll).
* Detectar tipos de variables automáticamente mediante IA offline (y online como alternativa).
* Realizar análisis de distribución de frecuencia con razonamiento automatizado sobre uso de datos agrupados (Sturges).
* Generar gráficos (histograma, polígono de frecuencia, diagrama de pastel).
* Calcular e interpretar medidas de tendencia central y dispersión.
* Documentar todo el proceso con fórmulas, decisiones algorítmicas y referencias.

Te avisaré cuando el informe esté listo para revisión y descarga.


# Programa Estadístico con Python y GUI (Guía Paso a Paso)

Este informe presenta el diseño detallado de un programa en Python con interfaz gráfica para análisis estadístico descriptivo. El sistema permitirá cargar datos (CSV, Excel o formulario manual), detectar automáticamente el tipo de variable (categórica, ordinal, discreta, continua) mediante IA local y/o heurísticas, decidir el agrupamiento de datos (usando la regla de Sturges), calcular tablas de frecuencias y estadísticos básicos, generar gráficos (histograma, polígono de frecuencia, pastel) y finalmente interpretar los resultados. Se documentan fórmulas, decisiones algorítmicas y se proponen librerías clave (pandas, matplotlib, scikit-learn, PyQt/Tkinter). Cada proceso se ejemplifica con referencias técnicas o académicas.

## 1. Arquitectura General del Programa

Se recomienda una arquitectura modular tipo MVC:

* **Modelo de Datos:** usa Pandas para cargar y almacenar datos en `DataFrame`. Por ejemplo, `pd.read_csv('archivo.csv')` lee ficheros CSV, y `pd.read_excel` hace lo mismo con Excel.
* **Procesamiento/Análisis:** módulos para detección de tipos, cálculo de estadísticos y distribución de frecuencias.
* **Interfaz de Usuario (GUI):** implementada con PyQt5 (o PyQt6/PySide) o Tkinter. Permite formularios modales con campos y barras de desplazamiento para ingreso manual, tablas para mostrar datos y botones para iniciar cálculos. PyQt ofrece diseños profesionales (con QtDesigner) mientras que Tkinter es más rápido de prototipar.
* **Controlador/Flujo:** conecta GUI y análisis, orquesta carga de archivos, aplicación de IA local y generación de salidas (tablas, gráficos, interpretaciones).

Para **rapidez de desarrollo y claridad de código** se recomienda estructurar el proyecto en funciones/métodos claros (carga de datos, inferencia de tipo, cálculo de frecuencias, gráficos, estadísticos) y usar entornos como Anaconda o pip para manejar dependencias (pandas, matplotlib, scikit-learn, PyQt o Tkinter).

## 2. Carga de Datos

El programa debe permitir tres vías de ingreso: (a) fichero CSV, (b) fichero Excel (.xlsx), (c) ingreso manual vía formulario. Se sugiere usar **pandas** para lectura de archivos:

* **CSV:** `pd.read_csv(ruta_archivo)` lee archivos CSV con delimitador coma.
* **Excel:** `pd.read_excel(ruta_archivo)` lee archivos Excel. Pandas soporta múltiples hojas y formatos.
* **Ingreso manual:** Crear un **formulario modal** con barras de desplazamiento (usando QtWidgets en PyQt o Frame+Scrollbar en Tkinter) que capture filas y columnas. Los datos ingresados se deben volcar a un `DataFrame`.

Tras cargar, el `DataFrame` contiene las columnas y filas de la muestra (sin asumir aun el tipo de variable). Es conveniente permitir recarga de datos o corrección manual si la detección automática falla.

## 3. Detección Automática del Tipo de Variable

Cada columna debe clasificarse como **categórica nominal, ordinal, numérica discreta o continua**. Proponemos dos enfoques:

* **Heurístico local (offline):** Analizar la serie de datos. Por ejemplo: determinar cuántos valores únicos (`n_unicos`) hay respecto al tamaño de la muestra (`N`). Si `n_unicos/N` es pequeño (e.g. <5%), probablemente es **categórica**. Esto coincide con la sugerencia de StackOverflow: *“si hay relativamente pocos valores únicos, la columna es probablemente categórica”*. Luego, entre las categóricas distinguir nominal vs ordinal (p.ej., si los valores tienen un orden natural conocido). Si la columna es numérica (`dtype` numérico) y tiene muchos valores únicos, es probablemente **continua** (la definición: puede tomar cualquier valor en un intervalo) o **discreta** (solo ciertos valores contables). Por ejemplo, el conteo de objetos es discreto, la altura de personas es continua.

  * Se puede usar reglas de oro: si los datos son enteros y `n_unicos` es pequeño, tratar como discreta; si son floats con decimales, continua.
* **IA local opcional:** entrenar un modelo de clasificación (p.ej. árbol de decisión, modelo bayesiano) a partir de ejemplos sintéticos o históricos para predecir tipo (categórica/continua, ordinal/no) según patrones de datos. Investigaciones recientes proponen métodos bayesianos complejos para detectar tipos estadísticos automáticamente; implementar ese nivel es opcional. Como alternativa se puede incluir una opción en el GUI para afinar la clasificación mediante conectividad externa (e.g. llamar a un servicio web de análisis de datos) si el entorno lo permite, pero manteniendo la funcionalidad básica 100% offline.

Sea cual sea el método, **permitir siempre al usuario revisar y corregir manualmente** el tipo detectado (p.ej. una lista desplegable por columna) para garantizar fiabilidad.

## 4. Agrupación de Datos y Regla de Sturges

Para datos numéricos continuos, decidimos si presentar datos individuales o agrupar en clases. Si hay **pocos datos** o muchos valores repetidos, puede no necesitarse agrupación; si hay muchos datos o se prefiere histograma, se agrupa. Para justificar el número de clases usamos la **regla de Sturges**, un método empírico clásico:

$$
k = 1 + 3.322\,\log_{10}(N) \quad\text{(Sturges)},
$$

donde $N$ es el tamaño de la muestra y $k$ el número sugerido de clases. Alternativamente se puede usar $k = 1 + \log_2(N)$, equivalente por cambio de base. Luego, el **intervalo de clase** se calcula como

$$
\text{Amplitud} = \frac{\max(x_i) - \min(x_i)}{k}.
$$

Este proceso garantiza clases de ancho uniforme. Como la regla de Sturges es empírica, siempre se debe redondear $k$ al entero más cercano (por exceso). Se documenta este método en textos estadísticos. Por ejemplo, para $N=50$ se obtiene $k \approx 1 + 3.322\log_{10}(50) = 7$ clases.

Tras calcular $k$ y la amplitud, definir las clases contiguas. Para cada clase hay:

* **Límites de clase nominales (LC):** por ejemplo 10–20, 20–30, etc.
* **Límites reales (exactos) de clase (LRC):** corrigen por ±0.5 unidades del instrumento si los datos son discretos. Por convención, el límite superior nominal se considera abierto (no incluir el extremo). Los límites reales son el punto medio entre clase y la siguiente. Ej.: clase 10–20 con unidad =1 tiene LRC 9.5–20.5. Para datos con otra unidad (UM), los límites reales se ajustan en ±UM/2.
* **Marca de clase (MC):** punto medio entre límites reales o nominales. Formalmente es la media aritmética de los límites de clase, es decir, $\text{MC} = (\text{Límite inferior real} + \text{límite superior real})/2$. Por ejemplo, para clase 10–20 con LRC 9.5–20.5, MC = 15.0.

En cuanto a **datos agrupados vs. no agrupados**, se puede permitir al usuario elegir. Si $k=1$ (caso trivial) o $k$ muy grande (a filas unitarias), es “no agrupado”. En general, si el ancho de clase calculado es menor que la precisión de medición, quizás es mejor no agrupar. De cualquier forma, la decisión final debe documentarse; la regla de Sturges justifica el número de clases elegido.

## 5. Cálculo de Distribuciones de Frecuencia

Con los datos ya agrupados (o no), se construye la **tabla de frecuencias**. En ella se incluyen:

* **Clase (intervalo):** límites nominales (LC).
* **Límites reales de clase (LRC):** se obtienen como se explicó (p.ej. restando $\tfrac{\text{UM}}{2}$ al límite inferior nominal y sumando $\tfrac{\text{UM}}{2}$ al superior).
* **Marca de clase (MC):** punto medio.
* **Frecuencia absoluta (fᵢ):** número de observaciones en cada clase. Definición: “el número de veces que aparece un valor en el conjunto”.
* **Frecuencia relativa (hᵢ):** proporción $h_i = f_i/N$, donde $N$ es total de datos. En porcentaje es $100\cdot f_i/N$.
* **Frecuencia acumulada (Fᵢ):** suma acumulativa de frecuencias absolutas hasta la clase i. Formalmente “la suma de las frecuencias absolutas de todos los valores inferiores o iguales al valor considerado”.
* **Frecuencia relativa acumulada (Hᵢ):** suma acumulativa de frecuencias relativas.

Además se calcula:

* **Rango:** diferencia entre máximo y mínimo. Simplificando, $R = \max(x_i) - \min(x_i)$.
* **Número de clases (NC):** es $k$ calculado (apoyado por Sturges).
* **Intervalo de clase (IC):** ancho de cada clase (amplitud), ya calculado.
* **Unidad de medida (UM):** por ejemplo “años”, “cm”, etc. Se muestra para informar qué significan los números.
* **UM/2:** la mitad de la unidad, utilizada para límites reales.

Se recomienda generar esta tabla automáticamente usando pandas. Por ejemplo, con `pd.cut(datos, bins=k)` se obtienen clases etiquetadas y luego `value_counts` da fᵢ. Luego se construye un `DataFrame` con columnas calculadas. Todas las fórmulas deben incluirse en la documentación (como se ha hecho arriba). Por ejemplo, la frecuencia relativa se obtiene con $h_i = f_i/N$.

**Referencias:** La estructura y terminología de la tabla sigue textos de estadística. La obtención de LRC se basa en definiciones de límites reales. La marca de clase (MC) como media de límites está documentada.

## 6. Generación de Gráficos Estadísticos

Se generan automáticamente los siguientes gráficos, usando **matplotlib**:

* **Histograma:** gráfico de barras cuyos ejes son valores (horizontal) vs frecuencia (vertical). Se implementa con `plt.hist(datos, bins=k)`. (Ver ejemplo en Fig. 1). Matplotlib agrupa los datos en los mismos intervalos usados en la tabla y dibuja las barras. El histograma visualiza la distribución de frecuencias absolutas. Su altura puede normalizarse si se pide densidad.
* **Polígono de frecuencia:** línea poligonal que une los pares (marca de clase, frecuencia). Es análogo al histograma. Tras calcular MC y fᵢ, se dibuja `plt.plot(list_of_MC, list_of_f)` conectando puntos con línea. (Se suele cerrar el polígono al eje horizontal añadiendo 0 en ambos extremos). Ikusmira define: “un polígono de frecuencias es una representación… con líneas que unen los puntos formados por las marcas de clase y las frecuencias correspondientes”.
* **Diagrama de pastel:** útil para variables categóricas. Con `plt.pie(vals, labels=etiquetas)` se dibuja un pastel donde cada porción corresponde a la frecuencia relativa de una categoría. Se etiqueta con categorías. Es importante sólo aplicar pastel si tiene sentido (pocas categorías nominales).

&#x20;*Figura:* Histograma de ejemplo usando Matplotlib (datos simulados). Observe cómo el eje X muestra el rango agrupado y el eje Y la frecuencia. El programa generará un gráfico similar al ejecutar `plt.hist`.

Se recomienda rotular ejes claramente, mostrar leyenda cuando convenga, y usar `plt.show()` o incrustar el gráfico en la GUI. Bibliotecas adicionales (seaborn, plotly) pueden mejorar estética, pero matplotlib es suficiente y estándar. Un ejemplo de código para histograma:

```python
import matplotlib.pyplot as plt
plt.hist(datos, bins=k, edgecolor='black', alpha=0.7)
plt.xlabel('Valor')
plt.ylabel('Frecuencia')
plt.title('Histograma de frecuencias')
plt.show()
```

Para el polígono, se usaría `plt.plot(mc_list, f_list, marker='o')`. Para el pastel: `plt.pie(f_categorias, labels=cat_nombres, autopct='%1.1f%%')`.

## 7. Medidas de Tendencia Central y Dispersión

El programa calcula las siguientes medidas, con fórmulas y referencias:

* **Media aritmética:** promedio de los datos. $\bar{x} = \frac{1}{N}\sum_{i=1}^N x_i$. Se calcula en Pandas con `df['col'].mean()`. Definición: “la media aritmética es la suma de un conjunto de valores dividida entre el número total de sumandos”. Es muy sensible a valores atípicos.

* **Mediana:** valor central de la muestra ordenada. Si $N$ es impar, es el dato en posición $(N+1)/2$; si es par, la media de los dos centrales. Pandas: `df['col'].median()`. Es robusta en distribuciones sesgadas, dando más relevancia en esos casos.

* **Moda:** valor que ocurre con mayor frecuencia. Pandas: `df['col'].mode()`. Wikipedia: “la moda es el valor que aparece con mayor frecuencia en un conjunto de datos”. En distribuciones agrupar no siempre tendrá moda única; en ese caso se informa la(s) mayor(es).

* **Rango:** máximo menos mínimo, $R = \max(x_i)-\min(x_i)$. Describe extensión total.

* **Varianza:** promedio de los cuadrados de las desviaciones respecto a la media. Para población, $\sigma^2 = \frac{1}{N}\sum (x_i-\bar{x})^2$. Para muestra, $\displaystyle s^2 = \frac{1}{N-1}\sum (x_i-\bar{x})^2$. Pandas usa por defecto *muestra*. La varianza se expresa en unidades al cuadrado. No hay cita textual simple en los enlaces consultados, pero se debe incluir la fórmula.

* **Desviación típica (estándar):** raíz cuadrada de la varianza, $\sigma$ (o $s$). Tiene la misma unidad que los datos. Pandas: `df['col'].std()`.

* **Coeficiente de variación (CV):** mide dispersión relativa: $CV = \frac{\sigma}{|\bar{x}|}\times 100\%$. Economipedia lo define: “se calcula dividiendo la desviación típica entre el valor absoluto de la media” y usualmente se expresa en %. Un CV bajo indica datos agrupados cerca de la media, un CV alto indica gran dispersión.

Todas estas medidas se calculan fácilmente con Pandas (o numpy) y se incluyen en el informe junto a su significado. Se recomienda incluir referencias, por ejemplo la descripción de media y su influencia en presencia de valores atípicos, y la interpretación del CV para ayudar en la interpretación posterior.

## 8. Interpretación de Resultados

Finalmente, el programa puede sugerir interpretaciones básicas:

* **Tendencia central:** Comparar media, mediana y moda revela forma de la distribución. Si media ≈ mediana, la distribución es aproximadamente simétrica; si difieren, existe asimetría (por ej. media > mediana indica sesgo positivo). Wikipedia señala que en distribuciones asimétricas la mediana puede describir mejor la tendencia central. La moda indica el valor más frecuente; si difiere mucho de la media, puede haber sesgos o categorías dominantes.
* **Dispersión:** Un rango alto o alta varianza relativa indica que los datos están muy dispersos. El **coeficiente de variación** pone la dispersión en contexto: un CV pequeño (p.ej. <10%) sugiere datos muy homogéneos alrededor de la media, mientras que un CV grande (e.g. >100%) indica gran variabilidad. Por ejemplo, para ingresos donde CV alto, se infiere desigualdad.
* **Gráficos:** El histograma revela la forma (simetría, sesgo, unimodalidad). El polígono refuerza esta visualización. El pastel (si se usó) mostrará la proporción de categorías: por ejemplo, si una categoría domina mucho, se ve claramente.
* **Relación con negocio/contexto:** Se debe vincular los estadísticos con el dominio de los datos. Por ejemplo, en datos de salud escolar (como el archivo de ejemplo `student_health_data_rows.csv`), interpretar si la mayoría de mediciones caen en rangos normales o si hay valores extremos preocupantes.

La interpretación recomendada aparece como texto en el GUI o en reportes impresos, siempre basada en definiciones estadísticas generales. Se debe alentar al usuario a comprobar posibles causas de outliers y considerar la necesidad de más análisis (test de normalidad, correlaciones, etc.) como mejora.

## 9. Implementación y Desarrollo

**Entorno de desarrollo:** Se sugiere crear un entorno virtual (conda o venv). Instalar dependencias: `pip install pandas matplotlib scikit-learn pyqt5` (o `tkinter` viene por defecto en Python). Pandas será la base de datos interna, matplotlib y quizá seaborn para gráficos, sklearn para apoyo en IA local (p.ej. validación de tipos), y PyQt/Tkinter para UI.

**Estructura del código:** Dividir en módulos/clases: e.g., `data_loader.py`, `type_detector.py`, `stats_calculator.py`, `plotter.py`, `gui.py`. Esto facilita mantenimiento. Documentar cada función con comentarios y referencias a las fórmulas usadas (por ejemplo, en `stats_calculator.py`, indicar “Media = Σx\_i/N”).

**Detección de tipo:** Implemente primero heurísticas con pandas (`.nunique()`, `.dtype`). Para **categóricas** puede convertir columnas tipo object a `'category'`. Para **ordinales**, se podría detectar patrones de escala (p.ej. strings con rangos) o dejar que el usuario ajuste. Un ejemplo de pseudocódigo:

```python
if df[col].dtype in [np.float, np.int]:
    unique = df[col].nunique()
    if unique/len(df) < 0.05:
        tipo = 'Discreta'
    else:
        tipo = 'Continua'
else:
    tipo = 'Categórica nominal u ordinal'
```

Estas reglas simples siguen la lógica de usuarios técnicos. Se puede complementar entrenando un modelo de sklearn (p.ej. SVM) si se dispone de ejemplos etiquetados.

**Cálculo de frecuencias:** Use `pd.cut` o `np.histogram` para definir bins y contar. P.ej.

```python
binned = pd.cut(df[col], bins=k)
freq_tab = binned.value_counts().sort_index()
```

Luego compute FR = F/N y Fa acumulada con `cumsum()`. Para variables no agrupadas, la “tabla de frecuencias” es simplemente los valores únicos y sus frecuencias. Mostrar la tabla en GUI (usando QTableView en PyQt o Treeview en Tkinter).

**Gráficos:** Directamente con matplotlib; los métodos ya descritos. También se puede usar tkinter.Canvas o PyQtGraph para integrar gráficos en la aplicación. Asegurarse de que los ejes sean legibles y que exista la opción de guardar como imagen o PDF.

**Medidas estadísticas:** Aprovechar pandas:

```python
media = df[col].mean()
mediana = df[col].median()
moda = df[col].mode()  # devuelve lista
varianza = df[col].var(ddof=0)  # poblacional
desv_std = df[col].std(ddof=0)
CV = desv_std/abs(media)
```

Mostrar estos resultados con sus unidades y, opcionalmente, interpretar (e.g. “la media es X, la mediana es Y, lo que indica distribución \[simétrica/sesgada]” basándose en comparación).

**Opcional offline/online:** Aunque el enfoque es offline (sin internet), se podría diseñar la arquitectura para permitir, con una bandera de configuración, enviar los datos a un servicio web de análisis (por ejemplo, un endpoint de IA) para mejoras en clasificación o gráficos avanzados. En ese caso documentarías la capa de conexión de forma abstracta (por ej. “si está habilitado, use requests a http\://servicio\_ia/detect” con manejo de errores). Sin conexión, el programa debe funcionar plenamente.

## 10. Conclusiones

Este programa integrará procesamiento de datos, IA local para tipado, análisis estadístico y visualización en un solo entorno. Con **pandas** gestionamos datos de forma eficiente, con **matplotlib** creamos visuales informativos, y **scikit-learn** puede asistir en la detección de patrones. La **interfaz gráfica** (PyQt/Tkinter) facilitará al usuario la interacción sin escribir código, logrando rapidez de uso. La clara estructuración en pasos permite al desarrollador implementar cada módulo con referencias a la teoría estadística (fórmulas y definiciones). Se enfatiza la **documentación** de cada proceso y la inclusión de fórmulas estadísticas, de manera que el código sea explícito y mantenible. Finalmente, las referencias académicas citadas validan la elección de métodos (Sturges para clases, definiciones de variables, etc.), ofreciendo respaldo teórico al desarrollo.

**Bibliografía:** (Se incluyen referencias usadas en este informe)

* Definiciones de variables: Minitab, Economipedia, Edulcorada.
* Tablas de frecuencia: definiciones de frecuencia absoluta, relativa y acumulada.
* Regla de Sturges: explicación de fórmula.
* Límites de clase y marca: conceptos de límites reales y marca de clase.
* Gráficos: referencias a funciones de matplotlib.
* Medidas estadísticas: definiciones de media, mediana, moda y CV.
* Interpretación: robustez de median vs media, dispersión relativa.

Todas estas fuentes respaldan las fórmulas y conceptos implementados en el programa.
