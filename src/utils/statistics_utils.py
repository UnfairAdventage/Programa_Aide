import numpy as np
import pandas as pd
from typing import Dict, Any

def mean(series: pd.Series) -> float:
    """
    Calcula la media aritmética.
    Fórmula: x̄ = (1/N) * Σxᵢ
    Referencia: https://es.wikipedia.org/wiki/Media_aritm%C3%A9tica
    """
    return series.mean()

def median(series: pd.Series) -> float:
    """
    Calcula la mediana.
    Referencia: https://es.wikipedia.org/wiki/Mediana
    """
    return series.median()

def mode(series: pd.Series) -> Any:
    """
    Calcula la moda (puede haber más de una).
    Referencia: https://es.wikipedia.org/wiki/Moda_(estad%C3%ADstica)
    """
    m = series.mode()
    return m.tolist() if len(m) > 1 else m.iloc[0]

def data_range(series: pd.Series) -> float:
    """
    Calcula el rango: R = max(xᵢ) - min(xᵢ)
    Referencia: https://es.wikipedia.org/wiki/Rango_(estad%C3%ADstica)
    """
    return series.max() - series.min()

def variance(series: pd.Series) -> float:
    """
    Calcula la varianza muestral.
    Fórmula: s² = (1/(N-1)) * Σ(xᵢ - x̄)²
    Referencia: https://es.wikipedia.org/wiki/Varianza
    """
    return series.var(ddof=1)

def std_dev(series: pd.Series) -> float:
    """
    Calcula la desviación estándar muestral.
    Fórmula: s = sqrt(varianza)
    Referencia: https://es.wikipedia.org/wiki/Desviaci%C3%B3n_t%C3%ADpica
    """
    return series.std(ddof=1)

def coef_variation(series: pd.Series) -> float:
    """
    Calcula el coeficiente de variación (CV).
    Fórmula: CV = s / |x̄| * 100%
    Referencia: https://economipedia.com/definiciones/coeficiente-de-variacion.html
    """
    mean_val = mean(series)
    std_val = std_dev(series)
    return (std_val / abs(mean_val)) * 100 if mean_val != 0 else float('nan')

def mean_deviation(series: pd.Series) -> float:
    """
    Calcula la desviación media (media de los valores absolutos respecto a la media aritmética).
    Fórmula: DM = (1/N) * Σ|xᵢ - x̄|
    Referencia: https://es.wikipedia.org/wiki/Desviaci%C3%B3n_media
    """
    mean_val = mean(series)
    return np.mean(np.abs(series - mean_val))

def all_stats(series: pd.Series) -> Dict[str, Any]:
    """
    Calcula todas las medidas de tendencia central y dispersión.
    Devuelve un diccionario con los valores y las fórmulas/referencias.
    """
    if not pd.api.types.is_numeric_dtype(series):
        vacio = ("No se puede calcular para variables cualitativas", "", "")
        moda = mode(series)
        return {
            'Moda': (moda, '', 'https://es.wikipedia.org/wiki/Moda_(estad%C3%ADstica)'),
            'Media aritmética': vacio,
            'Mediana': vacio,
            'Rango': vacio,
            'Varianza': vacio,
            'Desviación estándar': vacio,
            'Desviación media': vacio,
            'Coeficiente de variación (%)': vacio
        }
    return {
        'Media aritmética': (mean(series), 'x̄ = (1/N) * Σxᵢ', 'https://es.wikipedia.org/wiki/Media_aritm%C3%A9tica'),
        'Mediana': (median(series), '', 'https://es.wikipedia.org/wiki/Mediana'),
        'Moda': (mode(series), '', 'https://es.wikipedia.org/wiki/Moda_(estad%C3%ADstica)'),
        'Rango': (data_range(series), 'R = max(xᵢ) - min(xᵢ)', 'https://es.wikipedia.org/wiki/Rango_(estad%C3%ADstica)'),
        'Varianza': (variance(series), 's² = (1/(N-1)) * Σ(xᵢ - x̄)²', 'https://es.wikipedia.org/wiki/Varianza'),
        'Desviación estándar': (std_dev(series), 's = sqrt(varianza)', 'https://es.wikipedia.org/wiki/Desviaci%C3%B3n_t%C3%ADpica'),
        'Desviación media': (mean_deviation(series), 'DM = (1/N) * Σ|xᵢ - x̄|', 'https://es.wikipedia.org/wiki/Desviaci%C3%B3n_media'),
        'Coeficiente de variación (%)': (coef_variation(series), 'CV = s / |x̄| * 100%', 'https://economipedia.com/definiciones/coeficiente-de-variacion.html')
    } 