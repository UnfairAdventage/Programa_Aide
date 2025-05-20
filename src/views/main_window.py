from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox,
                             QTableWidget, QTableWidgetItem, QComboBox)
from PyQt6.QtCore import Qt
from src.views.manual_input_dialog import ManualInputDialog
from src.views.variable_type_dialog import VariableTypeDialog
from src.views.grouping_dialog import GroupingDialog
from src.views.frequency_dialog import FrequencyDialog, group_by_initial_pairs
from src.views.statistics_dialog import StatisticsDialog
from src.models.data_model import DataModel
from src.utils.variable_detector import VariableType
from src.utils.plot_utils import plot_histogram, plot_frequency_polygon, plot_pie
import matplotlib.pyplot as plt

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
        
        # Botón para ver medidas estadísticas
        self.stats_button = QPushButton("Medidas de Tendencia y Dispersión")
        self.stats_button.clicked.connect(self.show_statistics)
        self.stats_button.setEnabled(False)
        analysis_layout.addWidget(self.stats_button)
        
        # Botones de gráficos
        self.hist_button = QPushButton("Histograma")
        self.hist_button.clicked.connect(self.show_histogram)
        self.hist_button.setEnabled(False)
        analysis_layout.addWidget(self.hist_button)
        
        self.poly_button = QPushButton("Polígono de Frecuencia")
        self.poly_button.clicked.connect(self.show_frequency_polygon)
        self.poly_button.setEnabled(False)
        analysis_layout.addWidget(self.poly_button)
        
        self.pie_button = QPushButton("Diagrama de Pastel")
        self.pie_button.clicked.connect(self.show_pie_chart)
        self.pie_button.setEnabled(False)
        analysis_layout.addWidget(self.pie_button)
        
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
            
    def show_statistics(self):
        """Muestra el diálogo de medidas de tendencia central y dispersión"""
        if self.data_model.data is None:
            return
        column = self.column_combo.currentText()
        if not column:
            return
        var_type = self.data_model.variable_types.get(column)
        if var_type not in [VariableType.NUMERICAL_CONTINUOUS, VariableType.NUMERICAL_DISCRETE]:
            QMessageBox.warning(self, "Error", "Solo se pueden calcular medidas estadísticas para columnas numéricas.")
            return
        dialog = StatisticsDialog(self.data_model.data[column], self)
        dialog.exec()
        self.status_label.setText(f"Medidas estadísticas mostradas para {column}")
    
    def show_histogram(self):
        """Muestra el histograma de la columna seleccionada"""
        if self.data_model.data is None:
            return
        column = self.column_combo.currentText()
        if not column:
            return
        var_type = self.data_model.variable_types.get(column)
        series = self.data_model.data[column]
        if var_type in [VariableType.NUMERICAL_CONTINUOUS, VariableType.NUMERICAL_DISCRETE]:
            if column in self.data_model.grouped_data:
                intervals = self.data_model.grouped_data[column]['intervals']
                bins = [interval.lower_nominal for interval in intervals] + [intervals[-1].upper_nominal]
            else:
                intervals = self.data_model.grouping.create_class_intervals(series)
                bins = [interval.lower_nominal for interval in intervals] + [intervals[-1].upper_nominal]
            plt.figure(figsize=(8, 4))
            plt.hist(series, bins=bins, edgecolor='black', alpha=0.7, color='tab:blue')
            plt.xlabel(column)
            plt.ylabel('Frecuencia')
            plt.title('Histograma')
            plt.tight_layout()
            plt.show()
        else:
            series_str = series.astype(str)
            if series_str.nunique(dropna=True) > 15:
                grouped = group_by_initial_pairs(series_str)
                freq = grouped.value_counts().sort_index()
                x = freq.index
                y = freq.values
            else:
                freq = series_str.value_counts().sort_index()
                x = freq.index
                y = freq.values
            plt.figure(figsize=(8, 4))
            plt.bar(x, y, color='tab:blue', alpha=0.7)
            plt.xlabel(column)
            plt.ylabel('Frecuencia')
            plt.title('Histograma (Cualitativa)')
            plt.xticks(rotation=90)
            plt.tight_layout()
            plt.show()
        self.status_label.setText(f"Histograma mostrado para {column}")
    
    def show_frequency_polygon(self):
        """Muestra el polígono de frecuencia de la columna seleccionada"""
        if self.data_model.data is None:
            return
        column = self.column_combo.currentText()
        if not column:
            return
        var_type = self.data_model.variable_types.get(column)
        series = self.data_model.data[column]
        if var_type in [VariableType.NUMERICAL_CONTINUOUS, VariableType.NUMERICAL_DISCRETE]:
            distribution = self.data_model.get_frequency_distribution(column)
            mc = [interval.class_mark for interval in distribution.intervals]
            f = [distribution.absolute_freq[str(interval)] for interval in distribution.intervals]
            plt.figure(figsize=(8, 4))
            plt.plot(mc, f, marker='o', linestyle='-', color='tab:orange')
            plt.xlabel('Marca de clase')
            plt.ylabel('Frecuencia')
            plt.title('Polígono de Frecuencia')
            plt.tight_layout()
            plt.show()
        else:
            series_str = series.astype(str)
            if series_str.nunique(dropna=True) > 15:
                grouped = group_by_initial_pairs(series_str)
                freq = grouped.value_counts().sort_index()
                x = range(len(freq.index))
                y = freq.values
                labels = freq.index
            else:
                freq = series_str.value_counts().sort_index()
                x = range(len(freq.index))
                y = freq.values
                labels = freq.index
            plt.figure(figsize=(8, 4))
            plt.plot(x, y, marker='o', linestyle='-', color='tab:orange')
            plt.xticks(x, labels, rotation=90)
            plt.xlabel(column)
            plt.ylabel('Frecuencia')
            plt.title('Polígono de Frecuencia (Cualitativa)')
            plt.tight_layout()
            plt.show()
        self.status_label.setText(f"Polígono de frecuencia mostrado para {column}")
    
    def show_pie_chart(self):
        """Muestra el diagrama de pastel para variables categóricas"""
        if self.data_model.data is None:
            return
        column = self.column_combo.currentText()
        if not column:
            return
        var_type = self.data_model.variable_types.get(column)
        if var_type not in [VariableType.CATEGORICAL_NOMINAL, VariableType.CATEGORICAL_ORDINAL]:
            QMessageBox.information(self, "No válido", "El diagrama de pastel solo es válido para variables categóricas.")
            return
        series = self.data_model.data[column].astype(str)
        if series.nunique(dropna=True) > 15:
            grouped = group_by_initial_pairs(series)
            counts = grouped.value_counts().sort_index()
            plot_pie(counts.values, counts.index, title=f"Diagrama de pastel: {column} (agrupado por iniciales)")
        else:
            counts = series.value_counts()
            plot_pie(counts.values, counts.index, title=f"Diagrama de pastel: {column}")
        self.status_label.setText(f"Diagrama de pastel mostrado para {column}")
            
    def update_column_selector(self):
        """Actualiza el selector de columnas"""
        self.column_combo.clear()
        
        if self.data_model.data is None:
            self.column_combo.setEnabled(False)
            self.group_button.setEnabled(False)
            self.frequency_button.setEnabled(False)
            self.stats_button.setEnabled(False)
            self.hist_button.setEnabled(False)
            self.poly_button.setEnabled(False)
            self.pie_button.setEnabled(False)
            return
        # Agregar columnas numéricas y categóricas
        has_numeric = False
        has_categorical = False
        for column in self.data_model.data.columns:
            var_type = self.data_model.variable_types.get(column)
            if var_type in [VariableType.NUMERICAL_CONTINUOUS, VariableType.NUMERICAL_DISCRETE]:
                self.column_combo.addItem(column)
                has_numeric = True
            elif var_type in [VariableType.CATEGORICAL_NOMINAL, VariableType.CATEGORICAL_ORDINAL]:
                self.column_combo.addItem(column)
                has_categorical = True
        self.column_combo.setEnabled(True)
        self.group_button.setEnabled(has_numeric)
        self.frequency_button.setEnabled(has_numeric)
        self.stats_button.setEnabled(has_numeric)
        self.hist_button.setEnabled(has_numeric)
        self.poly_button.setEnabled(has_numeric)
        self.pie_button.setEnabled(has_categorical)
            
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
                col_name = df.columns[j]
                unique_count = df[col_name].nunique(dropna=True)
                # Si la columna es de nombres y pocos valores únicos, mostrar iniciales
                if 'nombre' in col_name.lower() and unique_count <= 15:
                    value = ''.join([w[0] for w in value.split() if w])
                # Si hay más de 15 valores únicos, mostrar solo la primera palabra
                elif unique_count > 15:
                    value = value.split()[0] if value else ''
                self.data_table.setItem(i, j, QTableWidgetItem(value))
                
        # Ajustar tamaño de columnas
        self.data_table.resizeColumnsToContents() 