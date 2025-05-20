import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from enum import Enum

class VariableType(Enum):
    CATEGORICAL_NOMINAL = "Categórica Nominal"
    CATEGORICAL_ORDINAL = "Categórica Ordinal"
    NUMERICAL_DISCRETE = "Numérica Discreta"
    NUMERICAL_CONTINUOUS = "Numérica Continua"

class VariableDetector:
    def __init__(self):
        self.ordinal_patterns = {
            'siempre': 5, 'nunca': 1,
            'excelente': 5, 'muy bueno': 4, 'bueno': 3, 'regular': 2, 'malo': 1,
            'totalmente de acuerdo': 5, 'de acuerdo': 4, 'neutral': 3, 'en desacuerdo': 2, 'totalmente en desacuerdo': 1
        }
        
    def detect_variable_types(self, df: pd.DataFrame) -> Dict[str, VariableType]:
        """
        Detecta automáticamente el tipo de cada variable en el DataFrame
        
        Args:
            df: DataFrame con los datos
            
        Returns:
            Dict con el tipo de cada variable
        """
        variable_types = {}
        
        for column in df.columns:
            # Obtener valores únicos no nulos
            unique_values = df[column].dropna().unique()
            
            # Si hay muy pocos valores únicos, probablemente sea categórica
            if len(unique_values) <= 10:
                # Verificar si es ordinal
                if self._is_ordinal(df[column]):
                    variable_types[column] = VariableType.CATEGORICAL_ORDINAL
                else:
                    variable_types[column] = VariableType.CATEGORICAL_NOMINAL
            else:
                # Verificar si es numérica
                if pd.api.types.is_numeric_dtype(df[column]):
                    # Verificar si es discreta o continua
                    if self._is_discrete(df[column]):
                        variable_types[column] = VariableType.NUMERICAL_DISCRETE
                    else:
                        variable_types[column] = VariableType.NUMERICAL_CONTINUOUS
                else:
                    # Por defecto, si no es numérica y tiene muchos valores únicos
                    variable_types[column] = VariableType.CATEGORICAL_NOMINAL
                    
        return variable_types
    
    def _is_ordinal(self, series: pd.Series) -> bool:
        """
        Determina si una serie es ordinal basándose en patrones conocidos
        """
        # Convertir a minúsculas para comparación
        values = series.astype(str).str.lower()
        
        # Verificar si los valores coinciden con patrones ordinales conocidos
        for pattern in self.ordinal_patterns.keys():
            if any(pattern in str(v).lower() for v in values):
                return True
                
        # Verificar si los valores son números secuenciales
        if pd.api.types.is_numeric_dtype(series):
            unique_values = sorted(series.dropna().unique())
            if len(unique_values) <= 5:  # Número arbitrario para considerar ordinal
                return True
                
        return False
    
    def _is_discrete(self, series: pd.Series) -> bool:
        """
        Determina si una serie numérica es discreta
        """
        # Si todos los valores son enteros
        if series.dropna().apply(lambda x: float(x).is_integer()).all():
            return True
            
        # Si el número de valores únicos es menor que el 10% del total
        unique_ratio = len(series.unique()) / len(series)
        if unique_ratio < 0.1:
            return True
            
        return False 