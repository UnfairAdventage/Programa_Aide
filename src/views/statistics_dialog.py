from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QTextEdit, QMessageBox)
from src.utils.statistics_utils import all_stats, format_substitution
from src.utils.variable_detector import VariableType
import pandas as pd

class StatisticsDialog(QDialog):
    def __init__(self, data: pd.Series, var_type=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Medidas de Tendencia Central y Dispersión")
        self.setMinimumSize(900, 600)
        
        self.data = data  # Guardar los datos para poder mostrarlos completos
        
        # Detectar tipo si no se pasa
        if var_type is None and hasattr(data, 'name') and hasattr(parent, 'data_model'):
            var_type = parent.data_model.variable_types.get(data.name)
        
        layout = QVBoxLayout(self)
        
        # Calcular estadísticas
        stats = all_stats(data)
        if var_type in [VariableType.CATEGORICAL_NOMINAL, VariableType.CATEGORICAL_ORDINAL]:
            # Solo mostrar la moda como medida de tendencia central
            moda = {k: v for k, v in stats.items() if k.lower().startswith('moda')}
            vacio = ("No se puede calcular para variables cualitativas", "", "", "")
            stats = {
                'Moda': list(moda.values())[0] if moda else vacio,
                'Media aritmética': vacio,
                'Mediana': vacio,
                'Rango': vacio,
                'Varianza': vacio,
                'Desviación estándar': vacio,
                'Coeficiente de variación (%)': vacio
            }
        
        # Tabla de medidas
        self.table = QTableWidget()
        self.table.setRowCount(len(stats))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Medida", "Valor", "Sustitución", "Fórmula", "Referencia"
        ])
        
        for i, (key, (value, substitution, formula, ref)) in enumerate(stats.items()):
            # Medida
            self.table.setItem(i, 0, QTableWidgetItem(key))
            
            # Valor
            if isinstance(value, float):
                self.table.setItem(i, 1, QTableWidgetItem(f"{value:.4f}"))
            elif isinstance(value, list):
                self.table.setItem(i, 1, QTableWidgetItem(", ".join(str(v) for v in value)))
            else:
                self.table.setItem(i, 1, QTableWidgetItem(str(value)))
            
            # Sustitución
            substitution_item = QTableWidgetItem(substitution)
            substitution_item.setToolTip("Haz clic para ver todos los datos")
            self.table.setItem(i, 2, substitution_item)
            
            # Fórmula
            self.table.setItem(i, 3, QTableWidgetItem(formula))
            
            # Referencia
            self.table.setItem(i, 4, QTableWidgetItem(ref))
        
        # Conectar el evento de clic en la celda
        self.table.cellClicked.connect(self.show_full_substitution)
        
        # Ajustar columnas
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)
        
        # Explicación
        explanation = QTextEdit()
        explanation.setReadOnly(True)
        if var_type in [VariableType.CATEGORICAL_NOMINAL, VariableType.CATEGORICAL_ORDINAL]:
            explanation.setHtml(
                "<b>Nota:</b> Para variables cualitativas solo se calcula la moda (valor más frecuente).<br>"
                "<a href='https://es.wikipedia.org/wiki/Moda_(estad%C3%ADstica)'>Moda</a>: valor más frecuente." )
        else:
            explanation.setHtml(
                "<b>Referencias:</b><br>"
                "<ul>"
                "<li><a href='https://es.wikipedia.org/wiki/Media_aritm%C3%A9tica'>Media aritmética</a>: sensible a valores atípicos.</li>"
                "<li><a href='https://es.wikipedia.org/wiki/Mediana'>Mediana</a>: robusta ante valores extremos.</li>"
                "<li><a href='https://es.wikipedia.org/wiki/Moda_(estad%C3%ADstica)'>Moda</a>: valor más frecuente.</li>"
                "<li><a href='https://es.wikipedia.org/wiki/Rango_(estad%C3%ADstica)'>Rango</a>: extensión total de los datos.</li>"
                "<li><a href='https://es.wikipedia.org/wiki/Varianza'>Varianza</a>: dispersión respecto a la media.</li>"
                "<li><a href='https://es.wikipedia.org/wiki/Desviaci%C3%B3n_t%C3%ADpica'>Desviación estándar</a>: raíz de la varianza.</li>"
                "<li><a href='https://es.wikipedia.org/wiki/Desviaci%C3%B3n_media'>Desviación media</a>: promedio de las desviaciones absolutas respecto a la media.</li>"
                "<li><a href='https://economipedia.com/definiciones/coeficiente-de-variacion.html'>Coeficiente de variación</a>: dispersión relativa (%).</li>"
                "</ul>"
            )
        layout.addWidget(explanation)
        
        # Botón cerrar
        button_layout = QHBoxLayout()
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
    def show_full_substitution(self, row: int, column: int):
        """Muestra la sustitución completa cuando se hace clic en la celda"""
        if column == 2:  # Columna de sustitución
            measure = self.table.item(row, 0).text()
            if measure != "Moda" or pd.api.types.is_numeric_dtype(self.data):
                # Mostrar todos los datos
                full_data = format_substitution(self.data, max_values=len(self.data))
                QMessageBox.information(self, f"Datos completos - {measure}", 
                                      f"Todos los datos utilizados:\n{full_data}")