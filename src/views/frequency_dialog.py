from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                             QGroupBox, QFormLayout, QInputDialog)
from PyQt6.QtCore import Qt
import pandas as pd
from src.utils.frequency_distribution import FrequencyDistribution
from src.utils.variable_detector import VariableType
import string
import matplotlib.pyplot as plt
import numpy as np
import os
from dotenv import load_dotenv
from google import genai
import socket
import ast
import re

# Función para agrupar por pares de iniciales
def group_by_initial_pairs(series):
    pairs = [(a, b) for a, b in zip(string.ascii_uppercase[::2], string.ascii_uppercase[1::2])]
    # Si hay letras impares, añadir la última
    if len(string.ascii_uppercase) % 2 != 0:
        pairs.append((string.ascii_uppercase[-1], ''))
    bins = []
    labels = []
    for a, b in pairs:
        if b:
            bins.append((a, b))
            labels.append(f"{a}-{b}")
        else:
            bins.append((a,))
            labels.append(f"{a}")
    # Asignar cada valor a un grupo
    def assign_group(val):
        if not val:
            return ''
        initial = val[0].upper()
        for (a, *b), label in zip(bins, labels):
            if initial == a or (b and initial == b[0]):
                return label
        return 'Otros'
    return series.apply(assign_group)

class FrequencyDialog(QDialog):
    def __init__(self, distribution: FrequencyDistribution, column_name=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Distribución de Frecuencias")
        self.setMinimumSize(800, 600)
        
        self.distribution = distribution
        self.column_name = column_name or "variable"
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Estadísticas resumen
        summary_group = QGroupBox("Estadísticas Resumen")
        summary_layout = QFormLayout()
        
        stats = distribution.get_summary_stats()
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                summary_layout.addRow(f"{key}:", QLabel(f"{value:.4f}"))
            else:
                summary_layout.addRow(f"{key}:", QLabel(str(value)))
            
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Tabla de frecuencias
        self.table = QTableWidget()
        self.update_table()
        layout.addWidget(self.table)
        
        # Botones
        button_layout = QHBoxLayout()
        self.close_button = QPushButton("Cerrar")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
        
        self.last_formula = None
        self.last_x = None
        self.last_y = None
        self.last_best = None

    def update_table(self):
        """Actualiza la tabla con la distribución de frecuencias"""
        # Valor por defecto
        df = self.distribution.to_dataframe()
        column = None
        data_model = None
        if hasattr(self.parent(), 'data_model') and hasattr(self.parent(), 'column_combo'):
            column = self.parent().column_combo.currentText()
            data_model = self.parent().data_model
        # Si es cualitativa, aplicar agrupación personalizada si existe
        if column and data_model:
            var_type = data_model.variable_types.get(column)
            if var_type in [VariableType.CATEGORICAL_NOMINAL, VariableType.CATEGORICAL_ORDINAL]:
                series = data_model.data[column].astype(str)
                mapping = data_model.get_qualitative_grouping(column)
                if mapping:
                    grouped = series.map(mapping).fillna(series)
                    freq_abs = grouped.value_counts().sort_index()
                    freq_rel = freq_abs / freq_abs.sum()
                    freq_acum = freq_abs.cumsum()
                    freq_rel_acum = freq_rel.cumsum()
                    df = pd.DataFrame({
                        'Grupo': freq_abs.index,
                        'Frecuencia Absoluta': freq_abs.values,
                        'Frecuencia Relativa': freq_rel.values,
                        'Frecuencia Acumulada': freq_acum.values,
                        'Frecuencia Relativa Acumulada': freq_rel_acum.values
                    })
                elif series.nunique(dropna=True) > 15:
                    from src.views.frequency_dialog import group_by_initial_pairs
                    grouped = group_by_initial_pairs(series)
                    freq_abs = grouped.value_counts().sort_index()
                    freq_rel = freq_abs / freq_abs.sum()
                    freq_acum = freq_abs.cumsum()
                    freq_rel_acum = freq_rel.cumsum()
                    df = pd.DataFrame({
                        'Inicial(es)': freq_abs.index,
                        'Frecuencia Absoluta': freq_abs.values,
                        'Frecuencia Relativa': freq_rel.values,
                        'Frecuencia Acumulada': freq_acum.values,
                        'Frecuencia Relativa Acumulada': freq_rel_acum.values
                    })
        # Ahora df siempre está definido
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)
        for i in range(len(df)):
            for j in range(len(df.columns)):
                value = df.iloc[i, j]
                if isinstance(value, float):
                    value = f"{value:.4f}"
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def fit_and_plot(self):
        # Obtener datos X, Y
        df = self.distribution.to_dataframe()
        if 'Marca de Clase' in df.columns:
            x = df['Marca de Clase'].values
        else:
            x = np.arange(len(df))
        y = df['Frecuencia Absoluta (fᵢ)'].values
        # Ajustar polinomios de grado 1 a 5
        from sklearn.preprocessing import PolynomialFeatures
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import r2_score
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
        # Seleccionar el mejor modelo (mayor R², sin sobreajuste)
        best = max(results, key=lambda r: r["R²"])  # O puedes elegir grado 3 si prefieres
        coef = best["Coeficientes"]
        intercept = best["Intercepto"]
        deg = best["Grado"]
        # Construir fórmula
        terms = [f"{coef[i]:+.4f}x^{i+1}" for i in range(len(coef)-1, -1, -1)]
        formula = "f(x) = " + " ".join(terms) + f" {intercept:+.4f}"
        self.last_formula = formula
        self.last_x = x
        self.last_y = y
        self.last_best = best
        # Mostrar fórmula
        QInputDialog.getMultiLineText(self, "Fórmula Ajustada", "Fórmula polinómica ajustada:", formula)
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
        self.explain_button.setEnabled(True)

    def explain_with_gemini(self):
        # Llama a Gemini para explicar la fórmula
        # Verificar conexión
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
        except OSError:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Sin conexión", "No se detectó conexión a internet. La explicación IA requiere acceso a la nube.")
            return
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error IA", "No se encontró GEMINI_API_KEY en el .env")
            return
        client = genai.Client(api_key=api_key)
        prompt = (
            f"Explica por qué la siguiente fórmula polinómica es la mejor para ajustar la frecuencia absoluta de estos datos. "
            f"Incluye el razonamiento estadístico y matemático, y menciona el valor de R².\n"
            f"Fórmula: {self.last_formula}\n"
            f"Datos X: {self.last_x.tolist()}\n"
            f"Datos Y: {self.last_y.tolist()}\n"
            f"R²: {self.last_best['R²']}\n"
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = response.text
        from PyQt6.QtWidgets import QMessageBox
        def safe_filename(s):
            return re.sub(r'[^a-zA-Z0-9_-]', '_', str(s))
        filename = f"Explicacion_Formula_para_{safe_filename(self.column_name)}.md"
        QMessageBox.information(self, "Explicación IA", f"La explicación se ha guardado en el archivo: {filename}")
        # Guardar la respuesta en un archivo de texto
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)