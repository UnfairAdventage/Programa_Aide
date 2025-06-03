from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QSpinBox, QTableWidget, QTableWidgetItem)
import pandas as pd

class ManualInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ingreso Manual de Datos")
        self.setMinimumSize(600, 400)
        
        # Variables para almacenar dimensiones
        self.rows = 0
        self.cols = 0
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Controles para dimensiones
        dim_layout = QHBoxLayout()
        
        # Número de filas
        rows_layout = QVBoxLayout()
        rows_layout.addWidget(QLabel("Número de Filas:"))
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 1000)
        self.rows_spin.valueChanged.connect(self.update_table)
        rows_layout.addWidget(self.rows_spin)
        dim_layout.addLayout(rows_layout)
        
        # Número de columnas
        cols_layout = QVBoxLayout()
        cols_layout.addWidget(QLabel("Número de Columnas:"))
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 100)
        self.cols_spin.valueChanged.connect(self.update_table)
        cols_layout.addWidget(self.cols_spin)
        dim_layout.addLayout(cols_layout)
        
        layout.addLayout(dim_layout)
        
        # Tabla para datos
        self.table = QTableWidget()
        layout.addWidget(self.table)
        
        # Botones
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("Aceptar")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
    def update_table(self):
        """Actualiza la tabla cuando cambian las dimensiones"""
        rows = self.rows_spin.value()
        cols = self.cols_spin.value()
        
        self.table.setRowCount(rows)
        self.table.setColumnCount(cols)
        
        # Establecer encabezados de columnas
        for i in range(cols):
            self.table.setHorizontalHeaderItem(i, QTableWidgetItem(f"Columna {i+1}"))
            
    def get_data(self) -> pd.DataFrame:
        """Obtiene los datos ingresados como DataFrame"""
        rows = self.rows_spin.value()
        cols = self.cols_spin.value()
        
        # Crear diccionario para el DataFrame
        data = {}
        for col in range(cols):
            column_data = []
            for row in range(rows):
                item = self.table.item(row, col)
                value = item.text() if item else ""
                column_data.append(value)
            data[f"Columna {col+1}"] = column_data
            
        return pd.DataFrame(data) 