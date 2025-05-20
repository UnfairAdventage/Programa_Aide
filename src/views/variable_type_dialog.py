from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                             QHeaderView)
from PyQt6.QtCore import Qt
from src.utils.variable_detector import VariableType

# Mapeo para mostrar solo dos tipos al usuario
DISPLAY_TYPE_MAP = {
    VariableType.CATEGORICAL_NOMINAL: 'Cualitativa',
    VariableType.CATEGORICAL_ORDINAL: 'Cualitativa',
    VariableType.NUMERICAL_DISCRETE: 'Cuantitativa',
    VariableType.NUMERICAL_CONTINUOUS: 'Cuantitativa',
}
REVERSE_DISPLAY_TYPE_MAP = {
    'Cualitativa': VariableType.CATEGORICAL_NOMINAL,
    'Cuantitativa': VariableType.NUMERICAL_CONTINUOUS,
}

class VariableTypeDialog(QDialog):
    def __init__(self, variable_types: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tipos de Variables")
        self.setMinimumSize(500, 400)
        
        self.variable_types = variable_types
        self.result_types = variable_types.copy()
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Instrucciones
        instructions = QLabel("Revise y corrija los tipos de variables detectados:")
        layout.addWidget(instructions)
        
        # Tabla para tipos de variables
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Variable", "Tipo"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Llenar tabla
        self.table.setRowCount(len(variable_types))
        for i, (var_name, var_type) in enumerate(variable_types.items()):
            # Nombre de la variable
            self.table.setItem(i, 0, QTableWidgetItem(var_name))
            # ComboBox para el tipo (solo dos opciones)
            type_combo = QComboBox()
            for display_type in ['Cuantitativa', 'Cualitativa']:
                type_combo.addItem(display_type)
                if display_type == DISPLAY_TYPE_MAP[var_type]:
                    type_combo.setCurrentText(display_type)
            type_combo.currentTextChanged.connect(
                lambda text, row=i: self.update_type(row, text))
            self.table.setCellWidget(i, 1, type_combo)
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
        
    def update_type(self, row: int, new_type: str):
        var_name = self.table.item(row, 0).text()
        # Almacenar como tipo detallado (por defecto: nominal para cualitativa, continua para cuantitativa)
        self.result_types[var_name] = REVERSE_DISPLAY_TYPE_MAP[new_type]
        
    def get_variable_types(self) -> dict:
        return self.result_types 