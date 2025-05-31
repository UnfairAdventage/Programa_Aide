import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from src.utils.variable_detector import VariableDetector, VariableType
from src.utils.data_grouping import DataGrouping, ClassInterval
from src.utils.frequency_distribution import FrequencyCalculator, FrequencyDistribution

class DataModel:
    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
        self.variable_types: Dict[str, VariableType] = {}
        self.detector = VariableDetector()
        self.grouping = DataGrouping()
        self.grouped_data: Dict[str, Dict] = {}  # Almacena datos agrupados por columna
        self.frequency_calculator = FrequencyCalculator()
        self.frequency_distributions: Dict[str, FrequencyDistribution] = {}
        # NUEVO: agrupaciones cualitativas personalizadas
        self.qualitative_groupings: Dict[str, Dict[str, str]] = {}
        
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
        
    def set_qualitative_grouping(self, column: str, mapping: Dict[str, str]):
        """
        Guarda el mapeo de agrupación cualitativa para una columna
        """
        self.qualitative_groupings[column] = mapping
        # Forzar recálculo de la distribución de frecuencias
        if column in self.frequency_distributions:
            del self.frequency_distributions[column]

    def get_qualitative_grouping(self, column: str) -> Optional[Dict[str, str]]:
        """
        Obtiene el mapeo de agrupación cualitativa para una columna
        """
        return self.qualitative_groupings.get(column)

    def recommend_qualitative_grouping_method(self, column: str) -> str:
        """
        Recomienda el mejor método de agrupación para una variable cualitativa
        """
        if self.data is None or column not in self.data.columns:
            return "manual"
        series = self.data[column].astype(str)
        n_unique = series.nunique(dropna=True)
        value_counts = series.value_counts()
        # Reglas simples de recomendación
        if n_unique > 30:
            return "inicial"  # Demasiadas categorías, mejor agrupar por inicial
        if value_counts.iloc[0] / value_counts.sum() > 0.5:
            return "frecuencia"  # Hay una categoría dominante
        if n_unique < 6:
            return "manual"  # Pocas categorías, mejor manual
        # Si hay muchas categorías poco frecuentes
        rare = (value_counts < max(2, 0.05 * len(series))).sum()
        if rare > n_unique * 0.5:
            return "frecuencia"
        return "manual"

    def get_frequency_distribution(self, column: str) -> Optional[FrequencyDistribution]:
        """
        Obtiene la distribución de frecuencias para una columna
        """
        if column in self.frequency_distributions:
            return self.frequency_distributions[column]
        if self.data is None or column not in self.data.columns:
            return None
        var_type = self.variable_types.get(column)
        if var_type in [VariableType.CATEGORICAL_NOMINAL, VariableType.CATEGORICAL_ORDINAL]:
            series = self.data[column].astype(str)
            # APLICAR AGRUPACIÓN CUALITATIVA SI EXISTE
            mapping = self.get_qualitative_grouping(column)
            if mapping:
                grouped = series.map(mapping).fillna(series)
                freq_abs = grouped.value_counts().sort_index()
            else:
                # Si hay más de 15 categorías, agrupar por pares de iniciales
                if series.nunique(dropna=True) > 15:
                    from src.views.frequency_dialog import group_by_initial_pairs
                    grouped = group_by_initial_pairs(series)
                    freq_abs = grouped.value_counts().sort_index()
                else:
                    freq_abs = series.value_counts().sort_index()
            total = freq_abs.sum()
            freq_rel = freq_abs / total
            freq_acum = freq_abs.cumsum()
            freq_rel_acum = freq_rel.cumsum()
            # Crear un objeto FrequencyDistribution simulado para compatibilidad
            class DummyInterval:
                def __init__(self, label):
                    self.label = label
                def __str__(self):
                    return str(self.label)
            intervals = [DummyInterval(label) for label in freq_abs.index]
            distribution = FrequencyDistribution(
                intervals=intervals,
                absolute_freq={str(i): v for i, v in zip(intervals, freq_abs.values)},
                relative_freq={str(i): v for i, v in zip(intervals, freq_rel.values)},
                cumulative_freq={str(i): v for i, v in zip(intervals, freq_acum.values)},
                cumulative_relative_freq={str(i): v for i, v in zip(intervals, freq_rel_acum.values)},
                measurement_unit=1.0,
                total_observations=total
            )
            self.frequency_distributions[column] = distribution
            return distribution
        # Si es cuantitativa, flujo normal
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

    def analyze_polynomial_function(self, coefficients: List[float], intercept: float) -> Dict[str, Any]:
        """
        Analiza una función polinómica y retorna sus características principales
        
        Args:
            coefficients: Lista de coeficientes del polinomio
            intercept: Término independiente
            
        Returns:
            Dict con el análisis de la función
        """
        from scipy import optimize
        
        # Crear función polinómica
        def f(x):
            return sum(c * x**i for i, c in enumerate(coefficients)) + intercept
            
        # Dominio
        domain = "ℝ (todos los números reales)"
        
        # Rango
        # Para polinomios de grado par, el rango depende del coeficiente principal
        degree = len(coefficients)
        if degree % 2 == 0:
            if coefficients[-1] > 0:
                range_min = optimize.minimize(f, 0).fun
                range = f"[{range_min:.4f}, ∞)"
            else:
                range_max = optimize.maximize(f, 0).fun
                range = f"(-∞, {range_max:.4f}]"
        else:
            range = "ℝ (todos los números reales)"
            
        # Puntos críticos
        if degree > 1:
            # Derivada
            def f_prime(x):
                return sum((i+1) * c * x**i for i, c in enumerate(coefficients[:-1]))
            
            # Encontrar raíces de la derivada
            critical_points = []
            try:
                roots = optimize.root(f_prime, 0).x
                for x in roots:
                    y = f(x)
                    critical_points.append((x, y))
            except:
                pass
        else:
            critical_points = []
            
        # Ordenada al origen
        y_intercept = f(0)
        
        # Análisis de comportamiento
        behavior = []
        
        # Analizar término principal
        if degree > 0:
            lead_coef = coefficients[-1]
            if degree % 2 == 0:  # Grado par
                if lead_coef > 0:
                    behavior.append("La función es una parábola que abre hacia arriba")
                else:
                    behavior.append("La función es una parábola que abre hacia abajo")
            else:  # Grado impar
                if lead_coef > 0:
                    behavior.append("La función crece sin límite cuando x → ∞ y decrece sin límite cuando x → -∞")
                else:
                    behavior.append("La función decrece sin límite cuando x → ∞ y crece sin límite cuando x → -∞")
                    
        # Analizar pendiente si es lineal
        if degree == 1:
            slope = coefficients[0]
            if slope > 0:
                behavior.append(f"La pendiente es {slope:.4f} y es positiva")
            else:
                behavior.append(f"La pendiente es {slope:.4f} y es negativa")
                
        # Analizar término independiente
        if intercept != 0:
            behavior.append(f"La función se desplaza {abs(intercept):.4f} unidades {'hacia arriba' if intercept > 0 else 'hacia abajo'}")
            
        return {
            "Dominio": domain,
            "Rango": range,
            "Puntos Críticos": critical_points,
            "Ordenada al Origen": y_intercept,
            "Comportamiento": behavior
        } 