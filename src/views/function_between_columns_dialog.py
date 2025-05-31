import numpy as np
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QRadioButton, QButtonGroup, QSpinBox, QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit)
from PyQt6.QtCore import Qt
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from dotenv import load_dotenv
import os
from google import genai
from pydantic import BaseModel

class FunctionBetweenColumnsDialog(QDialog):
    def __init__(self, data_model, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Función entre columnas")
        self.setMinimumSize(800, 600)
        self.data_model = data_model
        self.df = data_model.data
        self.parent = parent
        self.model = None
        self.poly = None
        self.degree = 1
        self.x_col = None
        self.y_col = None
        self.x_vals = None
        self.y_vals = None
        self.coef_ = None
        self.intercept_ = None
        self.r2 = None
        self.ia_suggestion = None
        self.ia_suggestion_markdown = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        # Selección de columnas
        col_layout = QHBoxLayout()
        col_layout.addWidget(QLabel("Variable independiente (X):"))
        self.x_combo = QComboBox()
        col_layout.addWidget(self.x_combo)
        col_layout.addWidget(QLabel("Variable dependiente (Y):"))
        self.y_combo = QComboBox()
        col_layout.addWidget(self.y_combo)
        layout.addLayout(col_layout)
        # Llenar combos con columnas numéricas
        num_cols = [c for c in self.df.columns if np.issubdtype(self.df[c].dtype, np.number)] if self.df is not None else []
        if not num_cols or len(num_cols) < 2:
            QMessageBox.warning(self, "Sin datos", "Debes cargar al menos dos columnas numéricas para usar esta función.")
            self.close()
            return
        self.x_combo.addItems(num_cols)
        self.y_combo.addItems(num_cols)
        if len(num_cols) >= 2:
            self.y_combo.setCurrentIndex(1)
        # Modo de ajuste
        mode_layout = QHBoxLayout()
        self.auto_radio = QRadioButton("Automático (mejor grado)")
        self.manual_radio = QRadioButton("Manual (grado)")
        self.auto_radio.setChecked(True)
        mode_layout.addWidget(self.auto_radio)
        mode_layout.addWidget(self.manual_radio)
        self.degree_spin = QSpinBox()
        self.degree_spin.setMinimum(1)
        self.degree_spin.setMaximum(10)
        self.degree_spin.setValue(1)
        self.degree_spin.setEnabled(False)
        mode_layout.addWidget(QLabel("Grado:"))
        mode_layout.addWidget(self.degree_spin)
        layout.addLayout(mode_layout)
        self.auto_radio.toggled.connect(lambda checked: self.degree_spin.setEnabled(not checked))
        # Botón de ajuste
        fit_button = QPushButton("Ajustar función")
        fit_button.clicked.connect(self.fit_function)
        layout.addWidget(fit_button)
        # Función ajustada (editable)
        self.formula_label = QLabel("")
        self.formula_label.setWordWrap(True)
        layout.addWidget(self.formula_label)
        self.formula_edit = QLineEdit()
        self.formula_edit.setPlaceholderText("Edita la función aquí en notación LaTeX, por ejemplo: f(x) = 0.9x - 60")
        layout.addWidget(self.formula_edit)
        # Tabla editable
        self.table = QTableWidget()
        layout.addWidget(self.table)
        # Análisis algebraico
        self.analysis_label = QLabel("")
        self.analysis_label.setWordWrap(True)
        layout.addWidget(self.analysis_label)
        # Botón de IA
        ia_button = QPushButton("Sugerir modelo con IA")
        ia_button.clicked.connect(self.suggest_with_ia)
        layout.addWidget(ia_button)
        # Botón de guardar
        save_button = QPushButton("Guardar análisis en Markdown")
        save_button.clicked.connect(self.save_markdown)
        layout.addWidget(save_button)
        # Botón de graficar
        plot_button = QPushButton("Graficar")
        plot_button.clicked.connect(self.plot_function)
        layout.addWidget(plot_button)
        # Inicializar
        self.x_combo.currentIndexChanged.connect(self.reset)
        self.y_combo.currentIndexChanged.connect(self.reset)
        self.reset()

    def reset(self):
        self.formula_label.setText("")
        self.analysis_label.setText("")
        self.table.clear()
        self.ia_suggestion = None
        self.ia_suggestion_markdown = None

    def fit_function(self):
        x_col = self.x_combo.currentText()
        y_col = self.y_combo.currentText()
        if x_col == y_col:
            QMessageBox.warning(self, "Error", "Las columnas deben ser diferentes.")
            return
        x = self.df[x_col].values.reshape(-1, 1)
        y = self.df[y_col].values
        # Ajuste automático o manual
        if self.auto_radio.isChecked():
            best_r2 = -np.inf
            best_deg = 1
            for deg in range(1, 6):
                poly = PolynomialFeatures(degree=deg, include_bias=False)
                X_poly = poly.fit_transform(x)
                model = LinearRegression().fit(X_poly, y)
                y_pred = model.predict(X_poly)
                r2 = r2_score(y, y_pred)
                if r2 > best_r2:
                    best_r2 = r2
                    best_deg = deg
                    best_model = model
                    best_poly = poly
            self.degree = best_deg
            self.model = best_model
            self.poly = best_poly
            self.r2 = best_r2
        else:
            deg = self.degree_spin.value()
            poly = PolynomialFeatures(degree=deg, include_bias=False)
            X_poly = poly.fit_transform(x)
            model = LinearRegression().fit(X_poly, y)
            y_pred = model.predict(X_poly)
            self.degree = deg
            self.model = model
            self.poly = poly
            self.r2 = r2_score(y, y_pred)
        self.x_col = x_col
        self.y_col = y_col
        self.x_vals = x.flatten()
        self.y_vals = y
        self.coef_ = self.model.coef_.tolist()
        self.intercept_ = self.model.intercept_
        # Mostrar fórmula
        terms = [f"{self.coef_[i]:+.4f}x^{i+1}" for i in range(len(self.coef_)-1, -1, -1)]
        formula_latex = f"f(x) = {' '.join(terms)} {self.intercept_:+.4f}"
        self.formula_label.setText(f"<b>Función ajustada:</b> <br><pre>$$\displaystyle {formula_latex}$$</pre><br><b>R²:</b> {self.r2:.4f} (grado {self.degree})")
        self.formula_edit.setText(formula_latex)
        # Tabla editable
        self.table.setRowCount(len(self.x_vals))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels([self.x_col, f"{self.y_col} estimado"])
        for i, xval in enumerate(self.x_vals):
            x_item = QTableWidgetItem(str(xval))
            y_item = QTableWidgetItem(f"{self.predict_y(xval):.4f}")
            self.table.setItem(i, 0, x_item)
            self.table.setItem(i, 1, y_item)
        self.table.itemChanged.connect(self.update_table)
        # Análisis algebraico
        analysis = self.parent.data_model.analyze_polynomial_function(self.coef_, self.intercept_)
        analysis_text = f"<b>Dominio:</b> {analysis['Dominio']}<br>"
        analysis_text += f"<b>Rango:</b> {analysis['Rango']}<br>"
        analysis_text += f"<b>Puntos críticos:</b> {', '.join(f'({x:.4f}, {y:.4f})' for x, y in analysis['Puntos Críticos']) if analysis['Puntos Críticos'] else 'No hay'}<br>"
        analysis_text += f"<b>Ordenada al origen:</b> {analysis['Ordenada al Origen']:.4f}<br>"
        analysis_text += f"<b>Comportamiento:</b> {'; '.join(analysis['Comportamiento'])}"
        self.analysis_label.setText(analysis_text)

    def predict_y(self, xval):
        X_poly = self.poly.transform(np.array([[float(xval)]]))
        return self.model.predict(X_poly)[0]

    def update_table(self, item):
        row = item.row()
        col = item.column()
        if col == 0:
            try:
                xval = float(self.table.item(row, 0).text())
                yval = self.predict_y(xval)
                self.table.blockSignals(True)
                self.table.setItem(row, 1, QTableWidgetItem(f"{yval:.4f}"))
                self.table.blockSignals(False)
            except Exception:
                pass

    def suggest_with_ia(self):
        # Lógica para sugerir modelo con Gemini AI
        x_col = self.x_combo.currentText()
        y_col = self.y_combo.currentText()
        x = self.df[x_col].values.tolist()
        y = self.df[y_col].values.tolist()
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            QMessageBox.critical(self, "Error IA", "No se encontró GEMINI_API_KEY en el .env")
            return
        class ModelSuggestion(BaseModel):
            model_type: str
            formula: str
            explanation: str
        client = genai.Client(api_key=api_key)
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
            f"Variable independiente: {x_col}\n"
            f"Variable dependiente: {y_col}\n"
            f"X: {x}\n"
            f"Y: {y}"
            "Always respond in Spanish."
        )
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": ModelSuggestion,
                },
            )
            suggestion: ModelSuggestion = response.parsed
            self.ia_suggestion = suggestion
            self.ia_suggestion_markdown = (
                f"## Sugerencia de modelo por IA\n"
                f"- **Tipo de modelo:** {suggestion.model_type}\n"
                f"- **Fórmula sugerida:** $${suggestion.formula}$$\n"
                f"- **Explicación:** {suggestion.explanation}\n"
            )
            # Reemplazar la función mostrada y editable por la sugerida
            self.formula_label.setText(f"<b>Función sugerida por IA:</b> <br><pre>$$\displaystyle {suggestion.formula}$$</pre>")
            self.formula_edit.setText(suggestion.formula)
        except Exception as e:
            QMessageBox.critical(self, "Error IA", f"Error al obtener sugerencia de IA: {str(e)}")

    def save_markdown(self):
        import re
        xvals = [self.table.item(i, 0).text() for i in range(self.table.rowCount())]
        yvals = [self.table.item(i, 1).text() for i in range(self.table.rowCount())]
        formula = self.formula_edit.text() if self.formula_edit.text().strip() else self.formula_label.text()
        analysis = self.analysis_label.text()
        markdown = f"# Análisis de función entre columnas\n\n## Función ajustada\n\n$$\displaystyle {formula}$$\n\n## Tabla de valores\n| {self.x_col} | {self.y_col} estimado |\n|---|---|\n" + "\n".join(f"| {x} | {y} |" for x, y in zip(xvals, yvals)) + f"\n\n## Análisis algebraico\n{analysis}\n"
        if self.ia_suggestion_markdown:
            markdown += f"\n{self.ia_suggestion_markdown}\n"
        def safe_filename(s):
            return re.sub(r'[^a-zA-Z0-9_-]', '_', str(s))
        filename = f"Funcion_{safe_filename(self.x_col)}_vs_{safe_filename(self.y_col)}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(markdown)
        QMessageBox.information(self, "Guardado", f"El análisis se ha guardado en {filename}")

    def plot_function(self):
        import matplotlib.pyplot as plt
        if self.x_col is None or self.y_col is None or self.model is None or self.poly is None:
            QMessageBox.warning(self, "Error", "Primero ajusta una función para poder graficar.")
            return
        x = self.df[self.x_col].values
        y = self.df[self.y_col].values
        x_plot = np.linspace(min(x), max(x), 200)
        X_plot_poly = self.poly.transform(x_plot.reshape(-1, 1))
        y_plot = self.model.predict(X_plot_poly)
        plt.figure(figsize=(8, 5))
        plt.scatter(x, y, color='blue', label='Datos originales')
        plt.plot(x_plot, y_plot, color='red', label='Función ajustada')
        plt.xlabel(self.x_col)
        plt.ylabel(self.y_col)
        plt.title(f'{self.y_col} vs {self.x_col}')
        plt.legend()
        plt.tight_layout()
        plt.show() 