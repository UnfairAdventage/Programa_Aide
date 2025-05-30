import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import string
from collections import defaultdict

@dataclass
class ClassInterval:
    """Representa un intervalo de clase con sus límites y marca de clase"""
    lower_nominal: float
    upper_nominal: float
    lower_real: float
    upper_real: float
    class_mark: float
    
    def __str__(self) -> str:
        return f"[{self.lower_nominal} - {self.upper_nominal})"

class DataGrouping:
    def __init__(self, measurement_unit: float = 1.0):
        """
        Inicializa el agrupador de datos
        
        Args:
            measurement_unit: Unidad de medición para ajustar límites reales
        """
        self.measurement_unit = measurement_unit
        
    def calculate_sturges_classes(self, data: pd.Series) -> Tuple[int, float]:
        """
        Calcula el número de clases usando la regla de Sturges y el ancho de clase
        
        Args:
            data: Serie de datos numéricos
            
        Returns:
            Tuple con (número de clases, ancho de clase)
        """
        n = len(data.dropna())
        if n <= 1:
            return 1, 0
            
        # Aplicar regla de Sturges
        k = 1 + 3.322 * np.log10(n)
        k = int(np.ceil(k))  # Redondear al entero superior
        
        # Calcular ancho de clase
        data_range = data.max() - data.min()
        class_width = data_range / k
        
        return k, class_width
        
    def create_class_intervals(self, data: pd.Series, 
                             num_classes: Optional[int] = None,
                             class_width: Optional[float] = None) -> List[ClassInterval]:
        """
        Crea los intervalos de clase para los datos
        
        Args:
            data: Serie de datos numéricos
            num_classes: Número de clases (opcional)
            class_width: Ancho de clase (opcional)
            
        Returns:
            Lista de intervalos de clase
            
        Raises:
            ValueError: Si los datos no son numéricos
        """
        # Validar que los datos sean numéricos
        if not pd.api.types.is_numeric_dtype(data):
            raise ValueError("Los datos deben ser numéricos para crear intervalos de clase")
            
        if num_classes is None or class_width is None:
            num_classes, class_width = self.calculate_sturges_classes(data)
            
        min_value = data.min()
        max_value = data.max() # Obtener el valor máximo real
        intervals = []
        decimals = 3  # O el número de decimales que prefieras
        
        for i in range(num_classes):
            lower_nominal = round(min_value + i * class_width, decimals)
            upper_nominal = round(lower_nominal + class_width, decimals)
            
            # Ajustar el último límite superior nominal para incluir el valor máximo
            if i == num_classes - 1:
                upper_nominal = round(max(upper_nominal, max_value), decimals) # Asegurar que cubra el máximo

            # Calcular límites reales
            lower_real = round(lower_nominal - (self.measurement_unit / 2), decimals)
            upper_real = round(upper_nominal + (self.measurement_unit / 2), decimals)
            
            # Calcular marca de clase
            class_mark = round((lower_real + upper_real) / 2, decimals)
            
            intervals.append(ClassInterval(
                lower_nominal=lower_nominal,
                upper_nominal=upper_nominal,
                lower_real=lower_real,
                upper_real=upper_real,
                class_mark=class_mark
            ))
            
        return intervals
        
    def calculate_frequencies(self, data: pd.Series,
                            intervals: List[ClassInterval]) -> Dict[str, int]:
        """
        Calcula las frecuencias para cada intervalo de clase usando pd.cut
        de manera robusta, asegurando que todos los datos se incluyan.

        Args:
            data: Serie de datos numéricos
            intervals: Lista de objetos ClassInterval

        Returns:
            Diccionario con frecuencias por intervalo (etiquetas de intervalo como claves)
        """
        # Asegurarse de trabajar con datos numéricos y eliminar NaNs
        numeric_data = data.dropna()
        if numeric_data.empty:
            return {}

        # Definir los bordes de los bins para pd.cut.
        # Usamos los límites inferiores de cada intervalo como bordes de inicio.
        # El último borde es el límite superior nominal del último intervalo + una pequeña tolerancia.
        bins = [interval.lower_nominal for interval in intervals] + [intervals[-1].upper_nominal + 1e-9]
        
        # Crear etiquetas para los intervalos usando la representación string de ClassInterval.
        interval_labels = [str(interval) for interval in intervals]
        
        try:
            # Usar pd.cut con right=False para obtener intervalos cerrados a la izquierda [a, b).
            # include_lowest=True asegura que el valor mínimo se incluya en el primer bin [min, ...).
            # La tolerancia en el último bin asegura que el valor máximo caiga dentro del último intervalo.
            cut_series = pd.cut(numeric_data, bins=bins, right=False, include_lowest=True, labels=interval_labels)

            # Contar las ocurrencias en cada bin
            frequencies_counts = cut_series.value_counts().sort_index()

            # Convertir a diccionario. Asegurar que todas las etiquetas de intervalo estén presentes, incluso con 0.
            frequencies = {str(label): frequencies_counts.get(label, 0) for label in interval_labels}

            # **Verificación final:** Aunque pd.cut debería hacerlo, una comprobación simple
            # para asegurarse de que el total coincide es útil.
            total_counted = sum(frequencies.values())
            total_data = len(numeric_data)

            if total_counted != total_data:
                 # Esto indica que algo *muy* inusual está pasando con los datos o los bordes.
                 # Lanzar una advertencia. No forzamos el total aquí para que el desajuste sea visible.
                 print(f"Advertencia: El conteo de frecuencias ({total_counted}) no coincide con el total de datos no nulos ({total_data}).")
                 # Podrías añadir una lógica para distribuir la diferencia si es crítico que el total sume.

        except Exception as e:
            print(f"Error al usar pd.cut: {e}")
            # Si pd.cut falla (lo cual sería raro ahora), retornar 0 frecuencias o la lógica manual previa si prefieres.
            frequencies = {str(label): 0 for label in interval_labels}

        return frequencies
        
    def should_group_data(self, data: pd.Series) -> bool:
        """
        Determina si los datos deberían agruparse
        
        Args:
            data: Serie de datos numéricos
            
        Returns:
            True si los datos deberían agruparse, False en caso contrario
        """
        n = len(data.dropna())
        if n <= 1:
            return False
            
        k, class_width = self.calculate_sturges_classes(data)
        
        # No agrupar si k es muy grande (casi una clase por dato)
        if k >= n * 0.8:
            return False
            
        # No agrupar si el ancho de clase es menor que la unidad de medición
        if class_width < self.measurement_unit:
            return False
            
        return True 

# Agrupación por inicial o pares de iniciales
def group_by_initial(series):
    # Por defecto: pares de iniciales
    pairs = [(a, b) for a, b in zip(string.ascii_uppercase[::2], string.ascii_uppercase[1::2])]
    if len(string.ascii_uppercase) % 2 != 0:
        pairs.append((string.ascii_uppercase[-1], ''))
    bins = []
    labels = []
    for a, b in pairs:
        if b:
            bins.append((a, b))
            labels.append(f"{a}-{b}")
        else:
            bins.append((a,))
            labels.append(f"{a}")
    def assign_group(val):
        if not val:
            return ''
        initial = val[0].upper()
        for (a, *b), label in zip(bins, labels):
            if initial == a or (b and initial == b[0]):
                return label
        return 'Otros'
    return series.apply(assign_group)

# Agrupación por frecuencia (alta, media, baja)
def group_by_frequency(series, n_groups=3):
    value_counts = series.value_counts()
    total = value_counts.sum()
    thresholds = [0.7, 0.3]  # Por defecto: top 70% alta, siguiente 30% media, resto baja
    freq_map = {}
    cum_sum = 0
    sorted_vals = value_counts.index.tolist()
    for val in sorted_vals:
        freq = value_counts[val]
        cum_sum += freq
        ratio = cum_sum / total
        if ratio <= thresholds[0]:
            freq_map[val] = 'Alta frecuencia'
        elif ratio <= sum(thresholds):
            freq_map[val] = 'Media frecuencia'
        else:
            freq_map[val] = 'Baja frecuencia'
    return series.map(freq_map).fillna('Baja frecuencia')

# Agrupación por similitud fonética/lexical (requiere diccionario de sinónimos)
def group_by_similarity(series, synonyms_dict=None):
    if synonyms_dict is None:
        # Por defecto, no agrupa nada
        return series
    reverse_map = {}
    for group, values in synonyms_dict.items():
        for v in values:
            reverse_map[v.lower()] = group
    return series.apply(lambda x: reverse_map.get(x.lower(), x))

# Agrupación por mapeo personalizado
def group_by_custom_mapping(series, mapping):
    return series.map(mapping).fillna(series)

# Recomendación de agrupación
def get_grouping_recommendation(series):
    n_unique = series.nunique(dropna=True)
    value_counts = series.value_counts()
    if n_unique > 30:
        return "inicial"
    if value_counts.iloc[0] / value_counts.sum() > 0.5:
        return "frecuencia"
    if n_unique < 6:
        return "manual"
    rare = (value_counts < max(2, 0.05 * len(series))).sum()
    if rare > n_unique * 0.5:
        return "frecuencia"
    return "manual" 