### 📋 Tabla Detallada de Tareas para el Programa de IA con Funcionalidad Online y Offline

| Nº | Tarea Principal                                 | Subtareas                                                                                                        | Descripción Detallada                                                                                                               |
| -- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| 1  | **Configuración Inicial del Proyecto**          | - Crear entorno virtual<br>- Instalar dependencias<br>- Crear estructura de carpetas                             | Usar `venv` o `poetry`, instalar `transformers`, `requests`, `torch`, etc. Crear carpetas como `utils/`, `models/`, `data/`, etc.   |
| 2  | **Verificar Conectividad a Internet**           | - Detectar conexión activa<br>- Manejar excepciones                                                              | Usar `requests.get("https://huggingface.co")` y capturar errores con `try-except`.                                                  |
| 3  | **Interfaz de Entrada de Datos**                | - En línea: entrada JSON<br>- Offline: entrada por terminal                                                      | Online: leer JSON de examen.<br>Offline: solicitar preguntas y opciones al usuario desde terminal o archivo local.                  |
| 4  | **Procesamiento del JSON del Examen**           | - Validar estructura<br>- Extraer preguntas y opciones                                                           | Verificar que el JSON tenga preguntas, opciones y respuestas (si se incluyen). Crear estructura interna de datos.                   |
| 5  | **Inicializar el Modelo de IA**                 | - Cargar desde Hugging Face<br>- Manejar modo offline                                                            | Usar modelos como `tiiuae/falcon-7b-instruct` o similares. Descargar si es necesario para uso local en caso de pérdida de conexión. |
| 6  | **Formular Prompt para cada Pregunta**          | - Construir prompt amigable para el modelo<br>- Formato estándar                                                 | Ejemplo: "Dada la siguiente pregunta y opciones, responde solo con la letra correcta: \nPregunta: ... \nA) ... B) ... C) ..."       |
| 7  | **Obtener Respuestas desde Hugging Face**       | - Realizar llamada API<br>- Procesar la respuesta<br>- Manejar errores                                           | Usar API de Hugging Face con `transformers.pipeline` o `Inference API` y manejar timeouts o errores de red.                         |
| 8  | **Modo Offline: Pedir entrada de usuario**      | - Solicitar pregunta<br>- Solicitar opciones<br>- Generar respuesta local si posible                             | Pedir al usuario la pregunta y opciones por consola. Enviar a modelo local si está descargado, o mostrar error.                     |
| 9  | **Validar y Formatear la Respuesta del Modelo** | - Limpiar output del modelo<br>- Detectar letra (A/B/C...) o frase                                               | Usar regex o parsing para quedarnos solo con la letra o texto de la opción elegida.                                                 |
| 10 | **Guardar Respuestas Generadas**                | - Guardar en archivo CSV o JSON<br>- Mostrar resumen en consola                                                  | Incluir pregunta, opciones, respuesta elegida por la IA y correcta si se sabe.                                                      |
| 11 | **Calcular Resultados (si hay claves)**         | - Comparar respuestas IA vs clave<br>- Calcular % de acierto                                                     | Si el JSON incluye las respuestas correctas, hacer comparación.                                                                     |
| 12 | **Interfaz de Usuario (CLI o GUI ligera)**      | - Menu CLI interactivo<br>- Opción para cargar archivo o ingresar manualmente                                    | Incluir menú para: cargar archivo JSON, ingresar pregunta manual, exportar respuestas, etc.                                         |
| 13 | **Documentación del Código**                    | - Docstrings<br>- README con instrucciones<br>- Comentarios clave                                                | Documentar funciones, instalación, uso en línea y offline, modelo utilizado, etc.                                                   |
| 14 | **Pruebas y Validaciones**                      | - Casos de prueba JSON válidos e inválidos<br>- Modo offline sin internet<br>- Modo online sin modelo descargado | Validar robustez ante errores de entrada, desconexión de red, etc.                                                                  |
| 15 | **Exportación de Resultados**                   | - CSV para análisis<br>- JSON con todas las respuestas<br>- Opción de imprimir por pantalla                      | Permitir al usuario guardar el resumen en un formato utilizable fácilmente para revisión.                                           |


### 📁 Estructura Recomendada del Proyecto

```
ia_examen/
│
├── main.py
├── requirements.txt
├── README.md
├── config.py
├── data/
│   └── examen.json
├── models/
│   └── modelo_local/
├── utils/
│   ├── io_utils.py
│   ├── internet_check.py
│   ├── prompt_builder.py
│   └── response_parser.py
└── outputs/
    └── resultados.csv
```

---

### ✅ Consideraciones Técnicas Adicionales

* **Modelo sugerido online:** `tiiuae/falcon-7b-instruct` o `mistralai/Mixtral-8x7B-Instruct-v0.1` (si tienes acceso).
* **Librerías clave:** `transformers`, `torch`, `requests`, `json`, `re`, `csv`.
* **Modo offline:** podrías incluir una versión liviana como `distilbert` o usar modelos ya descargados localmente con `AutoModelForCausalLM.from_pretrained()`.
