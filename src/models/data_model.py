import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from utils.variable_detector import VariableDetector, VariableType

class DataModel:
    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
        self.variable_types: Dict[str, VariableType] = {}
        self.detector = VariableDetector()
        
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