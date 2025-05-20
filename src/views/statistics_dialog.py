from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                             QGroupBox, QFormLayout, QTextEdit)
from PyQt6.QtCore import Qt
from src.utils.statistics_utils import all_stats
import pandas as pd

class StatisticsDialog(QDialog):
    def __init__(self, data: pd.Series, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Medidas de Tendencia Central y Dispersión")
        self.setMinimumSize(700, 500)
        
        # Calcular estadísticas
        stats = all_stats(data)
        
        layout = QVBoxLayout(self)
        
        # Tabla de medidas
        self.table = QTableWidget()
        self.table.setRowCount(len(stats))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Medida", "Valor", "Fórmula", "Referencia"
        ])
        for i, (key, (value, formula, ref)) in enumerate(stats.items()):
            self.table.setItem(i, 0, QTableWidgetItem(key))
            if isinstance(value, float):
                self.table.setItem(i, 1, QTableWidgetItem(f"{value:.4f}"))
            elif isinstance(value, list):
                self.table.setItem(i, 1, QTableWidgetItem(", ".join(str(v) for v in value)))
            else:
                self.table.setItem(i, 1, QTableWidgetItem(str(value)))
            self.table.setItem(i, 2, QTableWidgetItem(formula))
            self.table.setItem(i, 3, QTableWidgetItem(ref))
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)
        
        # Explicación
        explanation = QTextEdit()
        explanation.setReadOnly(True)
        explanation.setHtml(
            "<b>Referencias:</b><br>"
            "<ul>"
            "<li><a href='https://es.wikipedia.org/wiki/Media_aritm%C3%A9tica'>Media aritmética</a>: sensible a valores atípicos.</li>"
            "<li><a href='https://es.wikipedia.org/wiki/Mediana'>Mediana</a>: robusta ante valores extremos.</li>"
            "<li><a href='https://es.wikipedia.org/wiki/Moda_(estad%C3%ADstica)'>Moda</a>: valor más frecuente.</li>"
            "<li><a href='https://es.wikipedia.org/wiki/Rango_(estad%C3%ADstica)'>Rango</a>: extensión total de los datos.</li>"
            "<li><a href='https://es.wikipedia.org/wiki/Varianza'>Varianza</a>: dispersión respecto a la media.</li>"
            "<li><a href='https://es.wikipedia.org/wiki/Desviaci%C3%B3n_t%C3%ADpica'>Desviación estándar</a>: raíz de la varianza.</li>"
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