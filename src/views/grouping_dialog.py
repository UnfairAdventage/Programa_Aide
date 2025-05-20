from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QSpinBox, QDoubleSpinBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QCheckBox)
from PyQt6.QtCore import Qt
import pandas as pd
from utils.data_grouping import DataGrouping, ClassInterval

class GroupingDialog(QDialog):
    def __init__(self, data: pd.Series, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agrupación de Datos")
        self.setMinimumSize(600, 500)
        
        self.data = data
        self.grouping = DataGrouping()
        self.intervals = []
        self.frequencies = {}
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Opciones de agrupación
        options_layout = QHBoxLayout()
        
        # Unidad de medición
        unit_layout = QVBoxLayout()
        unit_layout.addWidget(QLabel("Unidad de Medición:"))
        self.unit_spin = QDoubleSpinBox()
        self.unit_spin.setRange(0.0001, 1000)
        self.unit_spin.setValue(1.0)
        self.unit_spin.setDecimals(4)
        self.unit_spin.valueChanged.connect(self.update_grouping)
        unit_layout.addWidget(self.unit_spin)
        options_layout.addLayout(unit_layout)
        
        # Número de clases
        classes_layout = QVBoxLayout()
        classes_layout.addWidget(QLabel("Número de Clases:"))
        self.classes_spin = QSpinBox()
        self.classes_spin.setRange(1, 100)
        self.classes_spin.valueChanged.connect(self.update_grouping)
        classes_layout.addWidget(self.classes_spin)
        options_layout.addLayout(classes_layout)
        
        # Ancho de clase
        width_layout = QVBoxLayout()
        width_layout.addWidget(QLabel("Ancho de Clase:"))
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0.0001, 1000)
        self.width_spin.setDecimals(4)
        self.width_spin.valueChanged.connect(self.update_grouping)
        width_layout.addWidget(self.width_spin)
        options_layout.addLayout(width_layout)
        
        layout.addLayout(options_layout)
        
        # Checkbox para usar regla de Sturges
        self.use_sturges = QCheckBox("Usar Regla de Sturges")
        self.use_sturges.setChecked(True)
        self.use_sturges.stateChanged.connect(self.toggle_sturges)
        layout.addWidget(self.use_sturges)
        
        # Tabla de frecuencias
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Intervalo", "Límite Inferior Real", "Límite Superior Real",
            "Marca de Clase", "Frecuencia"
        ])
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
        
        # Inicializar agrupación
        self.update_grouping()
        
    def toggle_sturges(self, state):
        """Activa/desactiva la regla de Sturges"""
        self.classes_spin.setEnabled(not state)
        self.width_spin.setEnabled(not state)
        self.update_grouping()
        
    def update_grouping(self):
        """Actualiza la agrupación y la tabla"""
        # Actualizar unidad de medición
        self.grouping.measurement_unit = self.unit_spin.value()
        
        # Calcular intervalos
        if self.use_sturges.isChecked():
            self.intervals = self.grouping.create_class_intervals(self.data)
        else:
            self.intervals = self.grouping.create_class_intervals(
                self.data,
                num_classes=self.classes_spin.value(),
                class_width=self.width_spin.value()
            )
            
        # Actualizar controles
        if self.intervals:
            self.classes_spin.setValue(len(self.intervals))
            self.width_spin.setValue(
                self.intervals[0].upper_nominal - self.intervals[0].lower_nominal
            )
            
        # Calcular frecuencias
        self.frequencies = self.grouping.calculate_frequencies(self.data, self.intervals)
        
        # Actualizar tabla
        self.update_table()
        
    def update_table(self):
        """Actualiza la tabla con los intervalos y frecuencias"""
        self.table.setRowCount(len(self.intervals))
        
        for i, interval in enumerate(self.intervals):
            # Intervalo
            self.table.setItem(i, 0, QTableWidgetItem(str(interval)))
            
            # Límites reales
            self.table.setItem(i, 1, QTableWidgetItem(f"{interval.lower_real:.4f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{interval.upper_real:.4f}"))
            
            # Marca de clase
            self.table.setItem(i, 3, QTableWidgetItem(f"{interval.class_mark:.4f}"))
            
            # Frecuencia
            freq = self.frequencies.get(str(interval), 0)
            self.table.setItem(i, 4, QTableWidgetItem(str(freq)))
            
        # Ajustar columnas
        self.table.resizeColumnsToContents()
        
    def get_grouping_info(self) -> dict:
        """
        Retorna información sobre la agrupación
        
        Returns:
            Dict con información de la agrupación
        """
        return {
            'intervals': self.intervals,
            'frequencies': self.frequencies,
            'measurement_unit': self.unit_spin.value(),
            'num_classes': len(self.intervals),
            'class_width': self.width_spin.value() if self.intervals else 0
        } 