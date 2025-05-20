import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from .data_grouping import ClassInterval

@dataclass
class FrequencyDistribution:
    """Representa una distribución de frecuencias para un conjunto de datos"""
    intervals: List[ClassInterval]
    absolute_freq: Dict[str, int]
    relative_freq: Dict[str, float]
    cumulative_freq: Dict[str, int]
    cumulative_relative_freq: Dict[str, float]
    measurement_unit: float
    total_observations: int
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convierte la distribución de frecuencias a un DataFrame
        
        Returns:
            DataFrame con la distribución de frecuencias
        """
        data = []
        # Detectar si es cualitativa (DummyInterval)
        if not hasattr(self.intervals[0], 'lower_real'):
            for interval in self.intervals:
                interval_str = str(interval)
                data.append({
                    'Grupo/Categoría': interval_str,
                    'Frecuencia Absoluta (fᵢ)': self.absolute_freq[interval_str],
                    'Frecuencia Relativa (hᵢ)': self.relative_freq[interval_str],
                    'Frecuencia Acumulada (Fᵢ)': self.cumulative_freq[interval_str],
                    'Frecuencia Relativa Acumulada (Hᵢ)': self.cumulative_relative_freq[interval_str]
                })
            return pd.DataFrame(data)
        # Si es cuantitativa, flujo normal
        for interval in self.intervals:
            interval_str = str(interval)
            data.append({
                'Clase': interval_str,
                'Límite Inferior Real': interval.lower_real,
                'Límite Superior Real': interval.upper_real,
                'Marca de Clase': interval.class_mark,
                'Frecuencia Absoluta (fᵢ)': self.absolute_freq[interval_str],
                'Frecuencia Relativa (hᵢ)': self.relative_freq[interval_str],
                'Frecuencia Acumulada (Fᵢ)': self.cumulative_freq[interval_str],
                'Frecuencia Relativa Acumulada (Hᵢ)': self.cumulative_relative_freq[interval_str]
            })
        return pd.DataFrame(data)
        
    def get_summary_stats(self) -> Dict[str, float]:
        """
        Calcula estadísticas resumen de la distribución
        
        Returns:
            Dict con estadísticas resumen
        """
        # Si los intervalos no tienen atributos numéricos, es cualitativa
        if not hasattr(self.intervals[0], 'upper_nominal'):
            return {
                'Rango': 'No se puede calcular',
                'Número de Clases': len(self.intervals),
                'Intervalo de Clase': 'No se puede calcular',
                'Unidad de Medida': 'No se puede calcular',
                'UM/2': 'No se puede calcular',
                'Total de Observaciones': self.total_observations
            }
        return {
            'Rango': max(interval.upper_nominal for interval in self.intervals) - 
                    min(interval.lower_nominal for interval in self.intervals),
            'Número de Clases': len(self.intervals),
            'Intervalo de Clase': self.intervals[0].upper_nominal - self.intervals[0].lower_nominal,
            'Unidad de Medida': self.measurement_unit,
            'UM/2': self.measurement_unit / 2,
            'Total de Observaciones': self.total_observations
        }

class FrequencyCalculator:
    def __init__(self):
        """Inicializa el calculador de frecuencias"""
        pass
        
    def calculate_distribution(self, data: pd.Series, 
                             intervals: List[ClassInterval],
                             measurement_unit: float) -> FrequencyDistribution:
        """
        Calcula la distribución de frecuencias para los datos
        
        Args:
            data: Serie de datos
            intervals: Lista de intervalos de clase
            measurement_unit: Unidad de medición
            
        Returns:
            Distribución de frecuencias
        """
        # Calcular frecuencias absolutas
        absolute_freq = {}
        for interval in intervals:
            count = len(data[(data >= interval.lower_nominal) & 
                           (data < interval.upper_nominal)])
            absolute_freq[str(interval)] = count
            
        # Calcular total de observaciones
        total = sum(absolute_freq.values())
        
        # Calcular frecuencias relativas
        relative_freq = {
            interval: freq / total 
            for interval, freq in absolute_freq.items()
        }
        
        # Calcular frecuencias acumuladas
        cumulative_freq = {}
        cumulative_relative_freq = {}
        running_sum = 0
        running_relative_sum = 0
        
        for interval in intervals:
            interval_str = str(interval)
            running_sum += absolute_freq[interval_str]
            running_relative_sum += relative_freq[interval_str]
            
            cumulative_freq[interval_str] = running_sum
            cumulative_relative_freq[interval_str] = running_relative_sum
            
        return FrequencyDistribution(
            intervals=intervals,
            absolute_freq=absolute_freq,
            relative_freq=relative_freq,
            cumulative_freq=cumulative_freq,
            cumulative_relative_freq=cumulative_relative_freq,
            measurement_unit=measurement_unit,
            total_observations=total
        ) 