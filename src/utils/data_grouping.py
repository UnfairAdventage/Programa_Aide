import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ClassInterval:
    """Representa un intervalo de clase con sus límites y marca de clase"""
    lower_nominal: float
    upper_nominal: float
    lower_real: float
    upper_real: float
    class_mark: float
    
    def __str__(self) -> str:
        return f"[{self.lower_nominal:.2f} - {self.upper_nominal:.2f})"

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
        """
        if num_classes is None or class_width is None:
            num_classes, class_width = self.calculate_sturges_classes(data)
            
        min_value = data.min()
        intervals = []
        
        for i in range(num_classes):
            lower_nominal = min_value + i * class_width
            upper_nominal = lower_nominal + class_width
            
            # Calcular límites reales
            lower_real = lower_nominal - (self.measurement_unit / 2)
            upper_real = upper_nominal + (self.measurement_unit / 2)
            
            # Calcular marca de clase
            class_mark = (lower_real + upper_real) / 2
            
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
        Calcula las frecuencias para cada intervalo de clase
        
        Args:
            data: Serie de datos numéricos
            intervals: Lista de intervalos de clase
            
        Returns:
            Diccionario con frecuencias por intervalo
        """
        frequencies = {}
        
        for interval in intervals:
            # Contar valores que caen en el intervalo
            count = len(data[(data >= interval.lower_nominal) & 
                           (data < interval.upper_nominal)])
            frequencies[str(interval)] = count
            
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