from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                             QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt
import pandas as pd
from utils.frequency_distribution import FrequencyDistribution

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
            summary_layout.addRow(f"{key}:", QLabel(f"{value:.4f}"))
            
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
        
        # Configurar tabla
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)
        
        # Llenar datos
        for i in range(len(df)):
            for j in range(len(df.columns)):
                value = df.iloc[i, j]
                if isinstance(value, float):
                    value = f"{value:.4f}"
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
                
        # Ajustar columnas
        self.table.resizeColumnsToContents()
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents) 