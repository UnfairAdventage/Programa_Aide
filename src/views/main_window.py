from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox,
                             QTableWidget, QTableWidgetItem, QComboBox, QDialog, QLineEdit)
from PyQt6.QtCore import Qt
from src.views.manual_input_dialog import ManualInputDialog
from src.views.variable_type_dialog import VariableTypeDialog
from src.views.grouping_dialog import GroupingDialog
from src.views.frequency_dialog import FrequencyDialog, group_by_initial_pairs
from src.views.statistics_dialog import StatisticsDialog
from src.models.data_model import DataModel
from src.utils.variable_detector import VariableType
from src.utils.plot_utils import plot_histogram
import matplotlib.pyplot as plt
from src.views.qualitative_grouping_dialog import QualitativeGroupingDialog
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import socket
import os
import re
from dotenv import load_dotenv
from google import genai
from .function_between_columns_dialog import FunctionBetweenColumnsDialog
from pydantic import BaseModel

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
        
        # NUEVO: Botón para agrupar cualitativa
        self.qual_group_button = QPushButton("Agrupar Cualitativa")
        self.qual_group_button.clicked.connect(self.show_qualitative_grouping)
        self.qual_group_button.setEnabled(False)
        analysis_layout.addWidget(self.qual_group_button)
        
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
        
        # NUEVO: Botón para ajustar función y graficar
        self.fit_button = QPushButton("Ajustar Función y Graficar")
        self.fit_button.clicked.connect(self.fit_and_plot)
        self.fit_button.setEnabled(False)
        analysis_layout.addWidget(self.fit_button)
        
        # Botón para crear función entre columnas
        self.function_between_columns_button = QPushButton("Crear función entre columnas")
        self.function_between_columns_button.clicked.connect(self.show_function_between_columns_dialog)
        self.function_between_columns_button.setEnabled(False)
        layout.addWidget(self.function_between_columns_button)
        
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
            
        var_type = self.data_model.variable_types.get(column)
        if var_type not in [VariableType.NUMERICAL_CONTINUOUS, VariableType.NUMERICAL_DISCRETE]:
            QMessageBox.warning(self, "Error", 
                              "La agrupación solo está disponible para variables numéricas.")
            return
            
        dialog = GroupingDialog(self.data_model.data[column], self)
        if dialog.exec():
            # Actualizar agrupación
            grouping_info = dialog.get_grouping_info()
            self.data_model.update_grouping(column, grouping_info)
            # Eliminar la distribución de frecuencias previa para forzar recálculo
            if column in self.data_model.frequency_distributions:
                del self.data_model.frequency_distributions[column]
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
            class_marks = [interval.class_mark for interval in intervals]
            plot_histogram(series, bins, class_marks=class_marks, xlabel=column, ylabel='Frecuencia', title='Histograma')
        else:
            series_str = series.astype(str)
            mapping = self.data_model.get_qualitative_grouping(column)
            if mapping:
                grouped = series_str.map(mapping).fillna(series_str)
                freq = grouped.value_counts().sort_index()
                x = freq.index
                y = freq.values
            elif series_str.nunique(dropna=True) > 15:
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
            mapping = self.data_model.get_qualitative_grouping(column)
            if mapping:
                grouped = series_str.map(mapping).fillna(series_str)
                freq = grouped.value_counts().sort_index()
                x = range(len(freq.index))
                y = freq.values
                labels = freq.index
            elif series_str.nunique(dropna=True) > 15:
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
        """Muestra el diagrama de pastel para variables categóricas y cuantitativas"""
        if self.data_model.data is None:
            return
        column = self.column_combo.currentText()
        if not column:
            return
        var_type = self.data_model.variable_types.get(column)
        series = self.data_model.data[column]

        if var_type in [VariableType.CATEGORICAL_NOMINAL, VariableType.CATEGORICAL_ORDINAL]:
            # Para variables categóricas
            series_str = series.astype(str)
            mapping = self.data_model.get_qualitative_grouping(column)
            if mapping:
                grouped = series_str.map(mapping).fillna(series_str)
                counts = grouped.value_counts().sort_index()
                from src.utils.plot_utils import plot_pie
                plot_pie(counts.values, counts.index, title=f"Diagrama de pastel: {column} (agrupado)")
            elif series_str.nunique(dropna=True) > 15:
                from src.views.frequency_dialog import group_by_initial_pairs
                grouped = group_by_initial_pairs(series_str)
                counts = grouped.value_counts().sort_index()
                from src.utils.plot_utils import plot_pie
                plot_pie(counts.values, counts.index, title=f"Diagrama de pastel: {column} (agrupado por iniciales)")
            else:
                counts = series_str.value_counts()
                from src.utils.plot_utils import plot_pie
                plot_pie(counts.values, counts.index, title=f"Diagrama de pastel: {column}")
        elif var_type in [VariableType.NUMERICAL_CONTINUOUS, VariableType.NUMERICAL_DISCRETE]:
            # Para variables cuantitativas
            distribution = self.data_model.get_frequency_distribution(column)
            if distribution:
                frequencies = [distribution.absolute_freq[str(interval)] for interval in distribution.intervals]
                labels = [f"{interval.lower_nominal:.2f} - {interval.upper_nominal:.2f}" for interval in distribution.intervals]
                from src.utils.plot_utils import plot_pie
                plot_pie(frequencies, labels, title=f"Diagrama de pastel: {column} (Frecuencias por intervalo)")
            else:
                QMessageBox.warning(self, "Error", "No se pudo calcular la distribución de frecuencias")
                return
        else:
            QMessageBox.information(self, "No válido", "El diagrama de pastel solo es válido para variables categóricas o cuantitativas.")
            return

        self.status_label.setText(f"Diagrama de pastel mostrado para {column}")
            
    def show_qualitative_grouping(self):
        """Muestra el diálogo de agrupación cualitativa"""
        if self.data_model.data is None:
            return
        column = self.column_combo.currentText()
        if not column:
            return
        var_type = self.data_model.variable_types.get(column)
        if var_type not in [VariableType.CATEGORICAL_NOMINAL, VariableType.CATEGORICAL_ORDINAL]:
            QMessageBox.warning(self, "Error", 
                                "La agrupación cualitativa solo está disponible para variables cualitativas.")
            return
        series = self.data_model.data[column].astype(str)
        recommendation = self.data_model.recommend_qualitative_grouping_method(column)
        dialog = QualitativeGroupingDialog(series, column, recommendation, self)
        if dialog.exec():
            mapping = dialog.get_mapping()
            self.data_model.set_qualitative_grouping(column, mapping)
            # Forzar recálculo de la distribución de frecuencias
            if column in self.data_model.frequency_distributions:
                del self.data_model.frequency_distributions[column]
            self.status_label.setText(f"Agrupación cualitativa aplicada para {column}")
            
    def update_column_selector(self):
        """Actualiza el selector de columnas"""
        self.column_combo.clear()
        
        if self.data_model.data is None:
            self.column_combo.setEnabled(False)
            self.group_button.setEnabled(False)
            self.qual_group_button.setEnabled(False)
            self.frequency_button.setEnabled(False)
            self.stats_button.setEnabled(False)
            self.hist_button.setEnabled(False)
            self.poly_button.setEnabled(False)
            self.pie_button.setEnabled(False)
            self.fit_button.setEnabled(False)
            self.function_between_columns_button.setEnabled(False)
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
        self.qual_group_button.setEnabled(has_categorical)
        self.frequency_button.setEnabled(has_numeric or has_categorical)
        self.stats_button.setEnabled(has_numeric)
        self.hist_button.setEnabled(has_numeric)
        self.poly_button.setEnabled(has_numeric)
        self.pie_button.setEnabled(has_numeric or has_categorical)
        self.fit_button.setEnabled(has_numeric)
        self.function_between_columns_button.setEnabled(True)
            
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
        
    def fit_and_plot(self):
        """Ajusta una función polinómica a los datos y muestra la gráfica"""
        if self.data_model.data is None:
            return
        column = self.column_combo.currentText()
        if not column:
            return
        var_type = self.data_model.variable_types.get(column)
        if var_type not in [VariableType.NUMERICAL_CONTINUOUS, VariableType.NUMERICAL_DISCRETE]:
            QMessageBox.warning(self, "Error", 
                              "El ajuste de función solo está disponible para variables numéricas.")
            return
            
        distribution = self.data_model.get_frequency_distribution(column)
        if not distribution:
            QMessageBox.warning(self, "Error", 
                              "No se pudo calcular la distribución de frecuencias")
            return
            
        # Obtener datos X, Y
        df = distribution.to_dataframe()
        if 'Marca de Clase' in df.columns:
            x = df['Marca de Clase'].values
        else:
            x = np.arange(len(df))
        y = df['Frecuencia Absoluta (fᵢ)'].values
        
        # Ajustar polinomios de grado 1 a 5
        results = []
        for deg in range(1, 6):
            poly = PolynomialFeatures(degree=deg, include_bias=False)
            X_poly = poly.fit_transform(x.reshape(-1, 1))
            model = LinearRegression().fit(X_poly, y)
            y_pred = model.predict(X_poly)
            r2 = r2_score(y, y_pred)
            results.append({
                "Grado": deg,
                "R²": round(r2, 4),
                "Coeficientes": model.coef_.tolist(),
                "Intercepto": round(model.intercept_, 4),
                "y_pred": y_pred
            })
            
        # Seleccionar el mejor modelo (mayor R²)
        best = max(results, key=lambda r: r["R²"])
        coef = best["Coeficientes"]
        intercept = best["Intercepto"]
        deg = best["Grado"]
        
        # Construir fórmula
        terms = [f"{coef[i]:+.4f}x^{i+1}" for i in range(len(coef)-1, -1, -1)]
        formula = "f(x) = " + " ".join(terms) + f" {intercept:+.4f}"
        
        # Guardar datos para la explicación IA (asegúrate de que siempre se asignen antes del diálogo)
        self.last_formula = formula
        self.last_x = x
        self.last_y = y
        self.last_best = best
        self.last_analysis = self.data_model.analyze_polynomial_function(coef, intercept)
        
        # Obtener análisis matemático
        analysis = self.data_model.analyze_polynomial_function(coef, intercept)
        
        # Crear contenido del archivo markdown
        markdown_content = f"""# Análisis de la Función Ajustada

## Fórmula
{formula}

## Análisis Matemático
- **Dominio**: {analysis['Dominio']}
- **Rango**: {analysis['Rango']}
- **Ordenada al Origen**: {analysis['Ordenada al Origen']:.4f}
- **Puntos Críticos**: {', '.join(f"({x:.4f}, {y:.4f})" for x, y in analysis['Puntos Críticos']) if analysis['Puntos Críticos'] else 'No hay puntos críticos'}

### Comportamiento
{chr(10).join('- ' + behavior for behavior in analysis['Comportamiento'])}

## Datos Originales
- **Datos X**: {x.tolist()}
- **Datos Y**: {y.tolist()}
- **R²**: {best['R²']}
"""
        
        # Guardar el análisis en un archivo
        def safe_filename(s):
            return re.sub(r'[^a-zA-Z0-9_-]', '_', str(s))
        filename = f"Analisis_Funcion_para_{safe_filename(column)}.md"
        # Si hay sugerencia de IA, añádela al markdown
        if hasattr(self, 'ia_suggestion_markdown') and self.ia_suggestion_markdown:
            markdown_content += f"\n{self.ia_suggestion_markdown}\n"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        # Crear diálogo personalizado para mostrar la fórmula y el análisis
        dialog = QDialog(self)
        dialog.setWindowTitle("Análisis de la Función Ajustada")
        layout = QVBoxLayout(dialog)
        
        # Mostrar fórmula
        formula_label = QLabel(formula)
        formula_label.setWordWrap(True)
        layout.addWidget(formula_label)
        # Campo editable para la función
        formula_edit = QLineEdit()
        formula_edit.setText(formula)
        formula_edit.setPlaceholderText("Edita la función aquí en notación LaTeX, por ejemplo: f(x) = 0.9x - 60")
        layout.addWidget(formula_edit)
        
        # Tabla de análisis
        analysis_table = QTableWidget()
        analysis_table.setObjectName("analysis_table")
        analysis_table.setRowCount(len(analysis))
        analysis_table.setColumnCount(2)
        analysis_table.setHorizontalHeaderLabels(["Característica", "Valor"])
        
        row = 0
        for key, value in analysis.items():
            analysis_table.setItem(row, 0, QTableWidgetItem(key))
            if isinstance(value, list):
                if key == "Puntos Críticos":
                    text = "\n".join(f"({x:.4f}, {y:.4f})" for x, y in value) if value else "No hay puntos críticos"
                else:
                    text = "\n".join(value)
            else:
                text = str(value)
            analysis_table.setItem(row, 1, QTableWidgetItem(text))
            row += 1
            
        analysis_table.resizeColumnsToContents()
        analysis_table.resizeRowsToContents()
        layout.addWidget(analysis_table)
        
        # Botones
        button_layout = QHBoxLayout()
        
        # Botón de explicación IA
        explain_button = QPushButton("Explicación IA")
        explain_button.clicked.connect(lambda: self.explain_with_gemini(dialog, analysis, markdown_content, x, y, best, formula_edit.text()))
        button_layout.addWidget(explain_button)
        # Botón de recomendar función con IA
        recommend_button = QPushButton("Recomendar función con IA")
        recommend_button.clicked.connect(lambda: self.recommend_function_with_ia(formula_label, formula_edit, x, y, column))
        button_layout.addWidget(recommend_button)
        # Botón de cerrar
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        dialog.exec()
        
        # Graficar
        fig = plt.figure(figsize=(8, 4))
        plt.scatter(x, y, color='blue', label='Frecuencia Absoluta (datos)')
        x_plot = np.linspace(min(x), max(x), 200)
        poly = PolynomialFeatures(degree=deg, include_bias=False)
        X_plot_poly = poly.fit_transform(x_plot.reshape(-1, 1))
        model = LinearRegression().fit(poly.fit_transform(x.reshape(-1, 1)), y)
        y_plot = model.predict(X_plot_poly)
        plt.plot(x_plot, y_plot, color='red', label='Función ajustada')
        plt.xlabel('Marca de Clase' if 'Marca de Clase' in df.columns else 'Índice de Grupo')
        plt.ylabel('Frecuencia Absoluta')
        plt.title('Ajuste polinómico a la frecuencia absoluta')
        plt.legend()
        plt.tight_layout()
        plt.show()
        
        # Traer la ventana de la gráfica al frente
        try:
            fig.canvas.manager.window.raise_()
            fig.canvas.manager.window.activateWindow()
        except Exception:
            pass
            
        self.status_label.setText(f"Función ajustada y graficada para {column}")
        
    def explain_with_gemini(self, parent_dialog=None, analysis=None, markdown_content=None, x=None, y=None, best=None, formula=None):
        """Genera una explicación de la fórmula ajustada usando IA"""
        # Verificar conexión
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
        except OSError:
            QMessageBox.warning(self, "Sin conexión", "No se detectó conexión a internet. La explicación IA requiere acceso a la nube.")
            return
        # Usar datos locales si los atributos de instancia no existen
        if formula is None:
            formula = getattr(self, 'last_formula', None)
        if x is None:
            x = getattr(self, 'last_x', None)
        if y is None:
            y = getattr(self, 'last_y', None)
        if best is None:
            best = getattr(self, 'last_best', None)
        if analysis is None:
            analysis = getattr(self, 'last_analysis', None)
        # Si aún falta alguno, mostrar error
        if formula is None or x is None or y is None or best is None or analysis is None:
            QMessageBox.warning(self, "Error", "No se encontraron los datos necesarios para la explicación IA. Por favor, ajusta una función primero.")
            return
            
        # Cargar API key
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            QMessageBox.critical(self, "Error IA", "No se encontró GEMINI_API_KEY en el .env")
            return
            
        # Generar explicación
        client = genai.Client(api_key=api_key)
        column = self.column_combo.currentText()
        
        # Generar explicación con IA
        prompt = (
            f"Análisis anterior: {analysis}\n"
            f"Explica por qué la siguiente fórmula polinómica es la mejor para ajustar la frecuencia absoluta de estos datos. "
            f"Incluye el razonamiento estadístico y matemático, y menciona el valor de R².\n"
            f"Fórmula: {formula}\n"
            f"Datos X: {x.tolist()}\n"
            f"Datos Y: {y.tolist()}\n"
            f"R²: {best['R²']}\n"
        )
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            text = response.text
            
            # Agregar explicación IA al contenido markdown
            markdown_content += "\n## Explicación IA\n" + text
            
            # Guardar la explicación en un archivo
            def safe_filename(s):
                return re.sub(r'[^a-zA-Z0-9_-]', '_', str(s))
            filename = f"Analisis_Funcion_para_{safe_filename(column)}.md"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(markdown_content)
                
            QMessageBox.information(self, "Análisis Completado", f"El análisis completo se ha guardado en el archivo: {filename}")
            
            # Si hay un diálogo padre, cerrarlo
            if parent_dialog:
                parent_dialog.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error IA", f"Error al generar la explicación: {str(e)}") 

    def recommend_function_with_ia(self, formula_label, formula_edit, x, y, column):
        """Usa Gemini para recomendar una nueva función y reemplaza la mostrada y editable si el usuario acepta. También actualiza la tabla de análisis y muestra la explicación."""
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            QMessageBox.critical(self, "Error IA", "No se encontró GEMINI_API_KEY en el .env")
            return
        class ModelAnalysis(BaseModel):
            formula: str
            model_type: str
            dominio: str
            rango: str
            puntos_criticos: list[str]
            ordenada_origen: str
            comportamiento: list[str]
            explicacion: str
        prompt = (
            "Para expresar algebraicamente la relación entre la temperatura y el consumo eléctrico de una ciudad, utilizamos una función donde el consumo depende de la temperatura. En este contexto:\n"
            "* Variable independiente: Temperatura ($x$)\n"
            "* Variable dependiente: Consumo eléctrico ($f(x)$)\n"
            "### 📘 Representación algebraica\n"
            "Una forma común de modelar esta relación es mediante una función cuadrática:\n"
            "$$f(x) = a \cdot x^2 + b \cdot x + c$$\n"
            "Donde:\n"
            "* $f(x)$: Consumo eléctrico en kilovatios-hora\n"
            "* $x$: Temperatura en grados Celsius\n"
            "* $a$, $b$, $c$: Coeficientes que ajustan la función al contexto específico\n"
            "Por ejemplo, si se determina que el consumo mínimo ocurre a 20°C y aumenta tanto para temperaturas más bajas como más altas, la función podría ser:\n"
            "$$f(x) = 2(x-20)^2 + 1000$$\n"
            "### 📊 Tabla de valores de ejemplo\n"
            "| Temperatura (°C) | Consumo estimado (kWh) |\n|------------------|------------------------|\n| 10               | 1200                   |\n| 15               | 1050                   |\n| 20               | 1000                   |\n| 25               | 1050                   |\n| 30               | 1200                   |\n"
            "Esta tabla muestra cómo el consumo estimado varía en función de la temperatura, según el modelo cuadrático propuesto.\n"
            "### 📌 Consideraciones adicionales\n"
            "Es importante destacar que la relación entre temperatura y consumo eléctrico puede no ser perfectamente cuadrática en la realidad. Factores como el uso de aire acondicionado, calefacción y hábitos de consumo pueden influir. Por ello, en algunos casos, se utilizan modelos más complejos para representar esta relación de manera más precisa.\n"
            "\nAhora, dada la siguiente relación entre dos variables, sugiere el mejor tipo de modelo matemático (lineal, polinómico [cuadrático, cúbico, etc.], exponencial, logarítmico, etc.), la fórmula ajustada en notación LaTeX y una breve explicación.\n"
            "formula (en LaTeX), model_type, dominio, rango, puntos_criticos (lista), ordenada_origen, comportamiento (lista), explicacion. "
            "Siempre responde en español. "
            f"Variable independiente: {column}\n"
            f"Variable dependiente: Frecuencia absoluta\n"
            f"X: {x.tolist()}\n"
            f"Y: {y.tolist()}\n"
        )
        client = genai.Client(api_key=api_key)
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": ModelAnalysis,
                },
            )
            analysis = response.parsed
            # Preguntar al usuario si quiere reemplazar
            msg = QMessageBox()
            msg.setWindowTitle("Sugerencia de función IA")
            msg.setText(f"La IA sugiere la siguiente función:\n\n$$ {analysis.formula} $$\n\n¿Deseas reemplazar la función actual y el análisis por esta sugerencia?\n\nExplicación: {analysis.explicacion}")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            ret = msg.exec()
            if ret == QMessageBox.StandardButton.Yes:
                # Actualizar función
                formula_label.setText(f"<b>Función sugerida por IA:</b> <br><pre>$$\displaystyle {analysis.formula}$$</pre>")
                formula_edit.setText(analysis.formula)
                # Actualizar solo la tabla de análisis (NO los datos originales del usuario)
                parent_dialog = formula_label.parentWidget().parentWidget() if hasattr(formula_label, 'parentWidget') else None
                if parent_dialog:
                    table = parent_dialog.findChild(QTableWidget, "analysis_table")
                    if table:
                        table.setRowCount(6)
                        table.setItem(0, 0, QTableWidgetItem("Dominio"))
                        table.setItem(0, 1, QTableWidgetItem(analysis.dominio))
                        table.setItem(1, 0, QTableWidgetItem("Rango"))
                        table.setItem(1, 1, QTableWidgetItem(analysis.rango))
                        table.setItem(2, 0, QTableWidgetItem("Puntos Críticos"))
                        table.setItem(2, 1, QTableWidgetItem(", ".join(analysis.puntos_criticos) if analysis.puntos_criticos else "No hay"))
                        table.setItem(3, 0, QTableWidgetItem("Ordenada al Origen"))
                        table.setItem(3, 1, QTableWidgetItem(analysis.ordenada_origen))
                        table.setItem(4, 0, QTableWidgetItem("Comportamiento"))
                        table.setItem(4, 1, QTableWidgetItem("; ".join(analysis.comportamiento)))
                        table.setItem(5, 0, QTableWidgetItem("Explicación"))
                        table.setItem(5, 1, QTableWidgetItem(analysis.explicacion))
                # Guardar explicación para el markdown si se guarda
                self.ia_suggestion_markdown = (
                    f"## Sugerencia de modelo por IA\n"
                    f"- **Tipo de modelo:** {analysis.model_type}\n"
                    f"- **Fórmula sugerida:** $${analysis.formula}$$\n"
                    f"- **Dominio:** {analysis.dominio}\n"
                    f"- **Rango:** {analysis.rango}\n"
                    f"- **Puntos críticos:** {', '.join(analysis.puntos_criticos) if analysis.puntos_criticos else 'No hay'}\n"
                    f"- **Ordenada al origen:** {analysis.ordenada_origen}\n"
                    f"- **Comportamiento:** {'; '.join(analysis.comportamiento)}\n"
                    f"- **Explicación:** {analysis.explicacion}\n"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error IA", f"Error al obtener sugerencia de IA: {str(e)}")

    def show_function_between_columns_dialog(self):
        """Muestra el diálogo para crear función entre columnas"""
        dialog = FunctionBetweenColumnsDialog(self.data_model, self)
        dialog.exec() 