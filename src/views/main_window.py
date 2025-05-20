from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QFileDialog)
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Programa Estadístico")
        self.setMinimumSize(800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        
        # Título
        title = QLabel("Programa de Análisis Estadístico")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Botón para cargar datos
        self.load_button = QPushButton("Cargar Datos")
        self.load_button.clicked.connect(self.load_data)
        layout.addWidget(self.load_button)
        
        # Área para mostrar datos y resultados
        self.data_label = QLabel("No hay datos cargados")
        self.data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.data_label)
        
    def load_data(self):
        """
        Maneja la carga de datos desde archivo
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de datos",
            "",
            "Archivos CSV (*.csv);;Archivos Excel (*.xlsx *.xls)"
        )
        
        if file_name:
            self.data_label.setText(f"Archivo seleccionado: {file_name}")
            # TODO: Implementar la carga de datos 