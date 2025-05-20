from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                             QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt
import pandas as pd
from src.utils.frequency_distribution import FrequencyDistribution
from src.utils.variable_detector import VariableType
import string

# Función para agrupar por pares de iniciales
def group_by_initial_pairs(series):
    pairs = [(a, b) for a, b in zip(string.ascii_uppercase[::2], string.ascii_uppercase[1::2])]
    # Si hay letras impares, añadir la última
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
    # Asignar cada valor a un grupo
    def assign_group(val):
        if not val:
            return ''
        initial = val[0].upper()
        for (a, *b), label in zip(bins, labels):
            if initial == a or (b and initial == b[0]):
                return label
        return 'Otros'
    return series.apply(assign_group)

class FrequencyDialog(QDialog):
    def __init__(self, distribution: FrequencyDistribution, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Distribución de Frecuencias")
        self.setMinimumSize(800, 600)
        
        self.distribution = distribution
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Estadísticas resumen
        summary_group = QGroupBox("Estadísticas Resumen")
        summary_layout = QFormLayout()
        
        stats = distribution.get_summary_stats()
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                summary_layout.addRow(f"{key}:", QLabel(f"{value:.4f}"))
            else:
                summary_layout.addRow(f"{key}:", QLabel(str(value)))
            
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Tabla de frecuencias
        self.table = QTableWidget()
        self.update_table()
        layout.addWidget(self.table)
        
        # Botones
        button_layout = QHBoxLayout()
        self.close_button = QPushButton("Cerrar")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
        
    def update_table(self):
        """Actualiza la tabla con la distribución de frecuencias"""
        df = self.distribution.to_dataframe()
        # Si la variable es cualitativa y hay más de 15 valores únicos, agrupar por pares de iniciales
        if hasattr(self.parent(), 'data_model') and hasattr(self.parent(), 'column_combo'):
            column = self.parent().column_combo.currentText()
            var_type = self.parent().data_model.variable_types.get(column)
            if var_type in [VariableType.CATEGORICAL_NOMINAL, VariableType.CATEGORICAL_ORDINAL]:
                original_series = self.parent().data_model.data[column].astype(str)
                if original_series.nunique(dropna=True) > 15:
                    grouped = group_by_initial_pairs(original_series)
                    freq_abs = grouped.value_counts().sort_index()
                    freq_rel = freq_abs / freq_abs.sum()
                    freq_acum = freq_abs.cumsum()
                    freq_rel_acum = freq_rel.cumsum()
                    # Construir DataFrame
                    df = pd.DataFrame({
                        'Inicial(es)': freq_abs.index,
                        'Frecuencia Absoluta': freq_abs.values,
                        'Frecuencia Relativa': freq_rel.values,
                        'Frecuencia Acumulada': freq_acum.values,
                        'Frecuencia Relativa Acumulada': freq_rel_acum.values
                    })
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)
        for i in range(len(df)):
            for j in range(len(df.columns)):
                value = df.iloc[i, j]
                if isinstance(value, float):
                    value = f"{value:.4f}"
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents) 