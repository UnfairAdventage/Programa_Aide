from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox,
                             QTableWidget, QTableWidgetItem, QComboBox)
from PyQt6.QtCore import Qt
from .manual_input_dialog import ManualInputDialog
from .variable_type_dialog import VariableTypeDialog
from .grouping_dialog import GroupingDialog
from .frequency_dialog import FrequencyDialog
from models.data_model import DataModel
from utils.variable_detector import VariableType

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
        
        # Botón para revisar tipos de variables
        self.review_types_button = QPushButton("Revisar Tipos de Variables")
        self.review_types_button.clicked.connect(self.show_variable_types)
        self.review_types_button.setEnabled(False)
        layout.addWidget(self.review_types_button)
        
        # Controles para análisis
        analysis_layout = QHBoxLayout()
        
        # Selector de columna
        analysis_layout.addWidget(QLabel("Columna:"))
        self.column_combo = QComboBox()
        self.column_combo.setEnabled(False)
        analysis_layout.addWidget(self.column_combo)
        
        # Botón para agrupar
        self.group_button = QPushButton("Agrupar Datos")
        self.group_button.clicked.connect(self.show_grouping)
        self.group_button.setEnabled(False)
        analysis_layout.addWidget(self.group_button)
        
        # Botón para ver frecuencias
        self.frequency_button = QPushButton("Ver Distribución de Frecuencias")
        self.frequency_button.clicked.connect(self.show_frequency_distribution)
        self.frequency_button.setEnabled(False)
        analysis_layout.addWidget(self.frequency_button)
        
        layout.addLayout(analysis_layout)
        
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
                self.review_types_button.setEnabled(True)
                self.update_column_selector()
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
            self.review_types_button.setEnabled(True)
            self.update_column_selector()
            self.status_label.setText("Datos ingresados manualmente")
            
    def show_variable_types(self):
        """Muestra el diálogo para revisar tipos de variables"""
        if self.data_model.data is None:
            return
            
        dialog = VariableTypeDialog(self.data_model.variable_types, self)
        if dialog.exec():
            # Actualizar tipos de variables
            new_types = dialog.get_variable_types()
            self.data_model.update_variable_types(new_types)
            self.update_column_selector()
            self.status_label.setText("Tipos de variables actualizados")
            
    def show_grouping(self):
        """Muestra el diálogo de agrupación"""
        if self.data_model.data is None:
            return
            
        column = self.column_combo.currentText()
        if not column:
            return
            
        dialog = GroupingDialog(self.data_model.data[column], self)
        if dialog.exec():
            # Actualizar agrupación
            grouping_info = dialog.get_grouping_info()
            self.data_model.update_grouping(column, grouping_info)
            self.status_label.setText(f"Datos agrupados para {column}")
            
    def show_frequency_distribution(self):
        """Muestra el diálogo de distribución de frecuencias"""
        if self.data_model.data is None:
            return
            
        column = self.column_combo.currentText()
        if not column:
            return
            
        distribution = self.data_model.get_frequency_distribution(column)
        if distribution:
            dialog = FrequencyDialog(distribution, self)
            dialog.exec()
            self.status_label.setText(f"Distribución de frecuencias mostrada para {column}")
        else:
            QMessageBox.warning(self, "Error", 
                              "No se pudo calcular la distribución de frecuencias")
            
    def update_column_selector(self):
        """Actualiza el selector de columnas"""
        self.column_combo.clear()
        
        if self.data_model.data is None:
            self.column_combo.setEnabled(False)
            self.group_button.setEnabled(False)
            self.frequency_button.setEnabled(False)
            return
            
        # Agregar solo columnas numéricas
        for column in self.data_model.data.columns:
            var_type = self.data_model.variable_types.get(column)
            if var_type in [VariableType.NUMERICAL_CONTINUOUS, 
                          VariableType.NUMERICAL_DISCRETE]:
                self.column_combo.addItem(column)
                
        self.column_combo.setEnabled(True)
        has_numeric_columns = self.column_combo.count() > 0
        self.group_button.setEnabled(has_numeric_columns)
        self.frequency_button.setEnabled(has_numeric_columns)
            
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