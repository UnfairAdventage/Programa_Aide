from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox,
                             QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt
from .manual_input_dialog import ManualInputDialog
from models.data_model import DataModel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Programa Estadístico")
        self.setMinimumSize(800, 600)
        
        # Inicializar el modelo de datos
        self.data_model = DataModel()
        
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
        
        # Botones para cargar datos
        buttons_layout = QHBoxLayout()
        
        self.load_csv_button = QPushButton("Cargar CSV")
        self.load_csv_button.clicked.connect(lambda: self.load_data("csv"))
        buttons_layout.addWidget(self.load_csv_button)
        
        self.load_excel_button = QPushButton("Cargar Excel")
        self.load_excel_button.clicked.connect(lambda: self.load_data("excel"))
        buttons_layout.addWidget(self.load_excel_button)
        
        self.manual_input_button = QPushButton("Ingreso Manual")
        self.manual_input_button.clicked.connect(self.show_manual_input)
        buttons_layout.addWidget(self.manual_input_button)
        
        layout.addLayout(buttons_layout)
        
        # Tabla para mostrar datos
        self.data_table = QTableWidget()
        layout.addWidget(self.data_table)
        
        # Etiqueta de estado
        self.status_label = QLabel("No hay datos cargados")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
    def load_data(self, file_type: str):
        """
        Maneja la carga de datos desde archivo
        
        Args:
            file_type: Tipo de archivo ('csv' o 'excel')
        """
        file_filter = "Archivos CSV (*.csv)" if file_type == "csv" else "Archivos Excel (*.xlsx *.xls)"
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            f"Seleccionar archivo {file_type.upper()}",
            "",
            file_filter
        )
        
        if file_name:
            if self.data_model.load_data(file_name):
                self.update_data_display()
                self.status_label.setText(f"Datos cargados exitosamente desde: {file_name}")
            else:
                QMessageBox.critical(self, "Error", "No se pudo cargar el archivo")
                
    def show_manual_input(self):
        """Muestra el diálogo de ingreso manual"""
        dialog = ManualInputDialog(self)
        if dialog.exec():
            # Obtener datos del diálogo
            df = dialog.get_data()
            self.data_model.data = df
            self.data_model._detect_variable_types()
            self.update_data_display()
            self.status_label.setText("Datos ingresados manualmente")
            
    def update_data_display(self):
        """Actualiza la tabla con los datos cargados"""
        if self.data_model.data is None:
            return
            
        df = self.data_model.data
        self.data_table.setRowCount(len(df))
        self.data_table.setColumnCount(len(df.columns))
        
        # Establecer encabezados
        self.data_table.setHorizontalHeaderLabels(df.columns)
        
        # Llenar datos
        for i in range(len(df)):
            for j in range(len(df.columns)):
                value = str(df.iloc[i, j])
                self.data_table.setItem(i, j, QTableWidgetItem(value))
                
        # Ajustar tamaño de columnas
        self.data_table.resizeColumnsToContents() 