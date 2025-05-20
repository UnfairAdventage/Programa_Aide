import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from utils.variable_detector import VariableDetector, VariableType
from utils.data_grouping import DataGrouping, ClassInterval
from utils.frequency_distribution import FrequencyCalculator, FrequencyDistribution

class DataModel:
    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
        self.variable_types: Dict[str, VariableType] = {}
        self.detector = VariableDetector()
        self.grouping = DataGrouping()
        self.grouped_data: Dict[str, Dict] = {}  # Almacena datos agrupados por columna
        self.frequency_calculator = FrequencyCalculator()
        self.frequency_distributions: Dict[str, FrequencyDistribution] = {}
        
    def load_data(self, file_path: str) -> bool:
        """
        Carga datos desde un archivo CSV o Excel
        
        Args:
            file_path: Ruta al archivo de datos
            
        Returns:
            bool: True si la carga fue exitosa, False en caso contrario
        """
        try:
            if file_path.endswith('.csv'):
                self.data = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                self.data = pd.read_excel(file_path)
            else:
                return False
                
            self._detect_variable_types()
            return True
        except Exception as e:
            print(f"Error al cargar datos: {str(e)}")
            return False
            
    def _detect_variable_types(self):
        """
        Detecta automáticamente el tipo de cada variable
        """
        if self.data is None:
            return
            
        self.variable_types = self.detector.detect_variable_types(self.data)
                
    def get_basic_stats(self, column: str) -> Dict[str, Any]:
        """
        Calcula estadísticas básicas para una columna
        
        Args:
            column: Nombre de la columna
            
        Returns:
            Dict con estadísticas básicas
        """
        if self.data is None or column not in self.data.columns:
            return {}
            
        stats = {
            'count': len(self.data[column]),
            'mean': self.data[column].mean(),
            'std': self.data[column].std(),
            'min': self.data[column].min(),
            'max': self.data[column].max()
        }
        
        return stats
        
    def update_variable_types(self, new_types: Dict[str, VariableType]):
        """
        Actualiza los tipos de variables
        
        Args:
            new_types: Nuevo diccionario de tipos de variables
        """
        self.variable_types = new_types
        
    def should_group_column(self, column: str) -> bool:
        """
        Determina si una columna debería agruparse
        
        Args:
            column: Nombre de la columna
            
        Returns:
            bool: True si la columna debería agruparse
        """
        if self.data is None or column not in self.data.columns:
            return False
            
        var_type = self.variable_types.get(column)
        if var_type not in [VariableType.NUMERICAL_CONTINUOUS, 
                          VariableType.NUMERICAL_DISCRETE]:
            return False
            
        return self.grouping.should_group_data(self.data[column])
        
    def get_grouped_data(self, column: str) -> Dict[str, Any]:
        """
        Obtiene los datos agrupados para una columna
        
        Args:
            column: Nombre de la columna
            
        Returns:
            Dict con información de agrupación
        """
        if column in self.grouped_data:
            return self.grouped_data[column]
            
        if not self.should_group_column(column):
            return {}
            
        intervals = self.grouping.create_class_intervals(self.data[column])
        frequencies = self.grouping.calculate_frequencies(self.data[column], intervals)
        
        self.grouped_data[column] = {
            'intervals': intervals,
            'frequencies': frequencies,
            'measurement_unit': self.grouping.measurement_unit,
            'num_classes': len(intervals),
            'class_width': intervals[0].upper_nominal - intervals[0].lower_nominal
        }
        
        return self.grouped_data[column]
        
    def update_grouping(self, column: str, grouping_info: Dict[str, Any]):
        """
        Actualiza la información de agrupación para una columna
        
        Args:
            column: Nombre de la columna
            grouping_info: Información de agrupación
        """
        self.grouped_data[column] = grouping_info 
        
    def get_frequency_distribution(self, column: str) -> Optional[FrequencyDistribution]:
        """
        Obtiene la distribución de frecuencias para una columna
        
        Args:
            column: Nombre de la columna
            
        Returns:
            Distribución de frecuencias o None si no hay datos
        """
        if column in self.frequency_distributions:
            return self.frequency_distributions[column]
            
        if self.data is None or column not in self.data.columns:
            return None
            
        # Si la columna está agrupada, usar esos intervalos
        if column in self.grouped_data:
            grouping_info = self.grouped_data[column]
            distribution = self.frequency_calculator.calculate_distribution(
                self.data[column],
                grouping_info['intervals'],
                grouping_info['measurement_unit']
            )
        else:
            # Si no está agrupada, crear intervalos usando Sturges
            intervals = self.grouping.create_class_intervals(self.data[column])
            distribution = self.frequency_calculator.calculate_distribution(
                self.data[column],
                intervals,
                self.grouping.measurement_unit
            )
            
        self.frequency_distributions[column] = distribution
        return distribution 