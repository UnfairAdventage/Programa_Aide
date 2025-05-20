# Programa Estadístico

Este es un programa de análisis estadístico con interfaz gráfica desarrollado en Python. Permite cargar datos, realizar análisis estadísticos descriptivos y generar visualizaciones.

## Características

- Carga de datos desde archivos CSV y Excel
- Detección automática de tipos de variables
- Cálculo de estadísticas descriptivas
- Generación de gráficos estadísticos
- Interfaz gráfica intuitiva

## Requisitos

- Python 3.8 o superior
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clonar el repositorio
2. Crear un entorno virtual (recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

Para ejecutar el programa:

```bash
python src/main.py
```

## Estructura del Proyecto

```
.
├── src/
│   ├── models/      # Modelos de datos
│   ├── views/       # Interfaces gráficas
│   ├── controllers/ # Controladores
│   └── utils/       # Utilidades
├── requirements.txt
└── README.md
```

## Licencia

Este proyecto está bajo la Licencia MIT. 