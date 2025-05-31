import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

def format_substitution(series: pd.Series, max_values: int = 5) -> str:
    """
    Formatea los datos para mostrar en la sustitución.
    Si hay más de max_values, muestra solo una parte y agrega '...'
    """
    values = series.dropna().tolist()
    # Detectar si los valores son numéricos
    is_numeric = pd.api.types.is_numeric_dtype(series)
    def format_value(x):
        return f"{x:.4f}" if is_numeric and isinstance(x, (int, float, np.integer, np.floating)) else str(x)
    if len(values) <= max_values:
        return ", ".join(format_value(x) for x in values)
    else:
        first_part = ", ".join(format_value(x) for x in values[:max_values])
        return f"{first_part} ... ({len(values)} valores en total)"

def mean(series: pd.Series) -> Tuple[float, str]:
    """
    Calcula la media aritmética.
    Fórmula: x̄ = (1/N) * Σxᵢ
    Referencia: https://es.wikipedia.org/wiki/Media_aritm%C3%A9tica
    """
    mean_val = series.mean()
    substitution = f"(1/{len(series)}) * ({format_substitution(series)})"
    return mean_val, substitution

def median(series: pd.Series) -> Tuple[float, str]:
    """
    Calcula la mediana.
    Referencia: https://es.wikipedia.org/wiki/Mediana
    """
    median_val = series.median()
    sorted_values = sorted(series.dropna())
    substitution = f"Mediana de [{format_substitution(pd.Series(sorted_values))}]"
    return median_val, substitution

def mode(series: pd.Series) -> Tuple[Any, str]:
    """
    Calcula la moda (puede haber más de una).
    Referencia: https://es.wikipedia.org/wiki/Moda_(estad%C3%ADstica)
    """
    m = series.mode()
    mode_val = m.tolist() if len(m) > 1 else m.iloc[0]
    substitution = f"Valor(es) más frecuente(s) en [{format_substitution(series)}]"
    return mode_val, substitution

def data_range(series: pd.Series) -> Tuple[float, str]:
    """
    Calcula el rango: R = max(xᵢ) - min(xᵢ)
    Referencia: https://es.wikipedia.org/wiki/Rango_(estad%C3%ADstica)
    """
    range_val = series.max() - series.min()
    substitution = f"{series.max():.4f} - {series.min():.4f}"
    return range_val, substitution

def variance(series: pd.Series) -> Tuple[float, str]:
    """
    Calcula la varianza muestral.
    Fórmula: s² = (1/(N-1)) * Σ(xᵢ - x̄)²
    Referencia: https://es.wikipedia.org/wiki/Varianza
    """
    mean_val = series.mean()
    variance_val = series.var(ddof=1)
    substitution = f"(1/{len(series)-1}) * Σ(xᵢ - x̄)²"
    return variance_val, substitution

def std_dev(series: pd.Series) -> Tuple[float, str]:
    """
    Calcula la desviación estándar muestral.
    Fórmula: s = sqrt(varianza)
    Referencia: https://es.wikipedia.org/wiki/Desviaci%C3%B3n_t%C3%ADpica
    """
    std_val = series.std(ddof=1)
    var_val = series.var(ddof=1)
    substitution = f"√{var_val:.4f}"
    return std_val, substitution

def coef_variation(series: pd.Series) -> Tuple[float, str]:
    """
    Calcula el coeficiente de variación (CV).
    Fórmula: CV = s / |x̄| * 100%
    Referencia: https://economipedia.com/definiciones/coeficiente-de-variacion.html
    """
    mean_val = mean(series)[0]
    std_val = std_dev(series)[0]
    # Redondear a 4 decimales para el cálculo y la sustitución
    mean_val_r = round(mean_val, 4)
    std_val_r = round(std_val, 4)
    cv_val = (std_val_r / abs(mean_val_r)) * 100 if mean_val_r != 0 else float('nan')
    substitution = f"({std_val_r:.4f} / |{mean_val_r:.4f}|) * 100%"
    return cv_val, substitution

def mean_deviation(series: pd.Series) -> Tuple[float, str]:
    """
    Calcula la desviación media (media de los valores absolutos respecto a la media aritmética).
    Fórmula: DM = (1/N) * Σ|xᵢ - x̄|
    Referencia: https://es.wikipedia.org/wiki/Desviaci%C3%B3n_media
    """
    mean_val = mean(series)[0]
    md_val = np.mean(np.abs(series - mean_val))
    substitution = f"(1/{len(series)}) * Σ|xᵢ - x̄|"
    return md_val, substitution

def all_stats(series: pd.Series) -> Dict[str, Tuple[Any, str, str, str]]:
    """
    Calcula todas las medidas de tendencia central y dispersión.
    Devuelve un diccionario con los valores, sustituciones, fórmulas y referencias.
    """
    if not pd.api.types.is_numeric_dtype(series):
        vacio = ("No se puede calcular para variables cualitativas", "", "", "")
        moda_val, moda_sub = mode(series)
        return {
            'Moda': (moda_val, moda_sub, 'Valor que más se repite en un grupo de datos', 'https://es.wikipedia.org/wiki/Moda_(estad%C3%ADstica)'),
            'Media aritmética': vacio,
            'Mediana': vacio,
            'Rango': vacio,
            'Varianza': vacio,
            'Desviación estándar': vacio,
            'Desviación media': vacio,
            'Coeficiente de variación (%)': vacio
        }

    mean_val, mean_sub = mean(series)
    median_val, median_sub = median(series)
    mode_val, mode_sub = mode(series)
    range_val, range_sub = data_range(series)
    var_val, var_sub = variance(series)
    std_val, std_sub = std_dev(series)
    md_val, md_sub = mean_deviation(series)
    cv_val, cv_sub = coef_variation(series)

    return {
        'Media aritmética': (mean_val, mean_sub, 'x̄ = (1/N) * Σxᵢ', 'https://es.wikipedia.org/wiki/Media_aritm%C3%A9tica'),
        'Mediana': (median_val, median_sub, 'Valor intermedio de un grupo de datos ordenados', 'https://es.wikipedia.org/wiki/Mediana'),
        'Moda': (mode_val, mode_sub, 'Valor que más se repite en un grupo de datos', 'https://es.wikipedia.org/wiki/Moda_(estad%C3%ADstica)'),
        'Rango': (range_val, range_sub, 'R = max(xᵢ) - min(xᵢ)', 'https://es.wikipedia.org/wiki/Rango_(estad%C3%ADstica)'),
        'Varianza': (var_val, var_sub, 's² = (1/(N-1)) * Σ(xᵢ - x̄)²', 'https://es.wikipedia.org/wiki/Varianza'),
        'Desviación estándar': (std_val, std_sub, 's = sqrt(varianza)', 'https://es.wikipedia.org/wiki/Desviaci%C3%B3n_t%C3%ADpica'),
        'Desviación media': (md_val, md_sub, 'DM = (1/N) * Σ|xᵢ - x̄|', 'https://es.wikipedia.org/wiki/Desviaci%C3%B3n_media'),
        'Coeficiente de variación (%)': (cv_val, cv_sub, 'CV = s / |x̄| * 100%', 'https://economipedia.com/definiciones/coeficiente-de-variacion.html')
    } 