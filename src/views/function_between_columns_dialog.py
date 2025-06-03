import numpy as np
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QRadioButton, QFormLayout, QSpinBox, QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QCheckBox, QDialogButtonBox)
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os
from google import genai
from pydantic import BaseModel
from src.utils.function_utils import (
    prepare_data,
    fit_polynomial,
    format_polynomial_formula,
    evaluate_modified_function,
    analyze_polynomial_function
)

# Esta clase representa una ventana de diálogo para realizar funciones entre columnas en un modelo de datos.
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
        self.function_ajustada_explanation = None
        self.undefined_vars = {}
        self.data_for_plot = None
        self.init_ui()

    def init_ui(self):
        """
        La función `init_ui` establece la interfaz de usuario para una herramienta de análisis de datos, lo que permite a los usuarios seleccionar
        Variables independientes y dependientes, ajustar modos de ajuste, editar fórmulas, analizar datos e interactuar
        con modelos de aprendizaje automático.
        : return: el método `init_ui` está devolviendo` none`.
        """
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
        # Checkbox para datos repetidos
        self.repeated_checkbox = QCheckBox("Usar promedio para datos repetidos (sin duplicados)")
        self.repeated_checkbox.setChecked(True)
        layout.addWidget(self.repeated_checkbox)
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
        # Botón de analizar función ajustada con IA
        analyze_ajustada_ia_button = QPushButton("Analizar función ajustada con IA")
        analyze_ajustada_ia_button.clicked.connect(self.analyze_ajustada_with_ia)
        layout.addWidget(analyze_ajustada_ia_button)
        # Inicializar
        self.x_combo.currentIndexChanged.connect(self.reset)
        self.y_combo.currentIndexChanged.connect(self.reset)
        self.reset()

    def clear_model_memory(self):
        """Limpia la memoria del modelo para evitar confusiones con funciones anteriores"""
        self.model = None
        self.poly = None
        self.coef_ = None
        self.intercept_ = None
        self.r2 = None
        self.undefined_vars = {}
        self.formula_label.setText("")
        self.formula_edit.setText("")
        self.analysis_label.setText("")
        self.table.clear()

    def fit_function(self):
        """
        El método `fit_function` se ajusta a una función polinomial a los datos, muestra la fórmula y el análisis
        Resultados, y actualiza una tabla con los valores ajustados.
        : return: el método `fit_function` no devuelve nada explícitamente, ya que no tiene un` retorno`
        declaración al final de la función.
        """
        x_col = self.x_combo.currentText()
        y_col = self.y_combo.currentText()
        if x_col == y_col:
            QMessageBox.warning(self, "Error", "Las columnas deben ser diferentes.")
            return

        # Limpiar memoria del modelo anterior
        self.clear_model_memory()

        # Preparar datos usando las utilidades
        x, y, self.data_for_plot = prepare_data(
            self.df, 
            x_col, 
            y_col, 
            self.repeated_checkbox.isChecked()
        )

        # Ajustar polinomio usando las utilidades
        fit_result = fit_polynomial(
            x, 
            y, 
            degree=self.degree_spin.value() if not self.auto_radio.isChecked() else None,
            auto_fit=self.auto_radio.isChecked()
        )

        # Guardar resultados
        self.model = fit_result['model']
        self.poly = fit_result['poly']
        self.degree = fit_result['degree']
        self.r2 = fit_result['r2']
        self.coef_ = fit_result['coef']
        self.intercept_ = fit_result['intercept']
        self.x_col = x_col
        self.y_col = y_col
        self.x_vals = x.flatten()
        self.y_vals = y

        # Formatear fórmula usando las utilidades
        formula_latex, self.undefined_vars = format_polynomial_formula(self.coef_, self.intercept_)
        self.formula_label.setText(f"<b>Función ajustada:</b> <br><pre>$$\displaystyle {formula_latex}$$</pre><br><b>R²:</b> {self.r2:.4f} (grado {self.degree})")
        self.formula_edit.setText(formula_latex)
        self.formula_ajustada_latex = formula_latex

        # Actualizar tabla
        self.table.setRowCount(len(self.x_vals))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels([self.x_col, f"{self.y_col} estimado"])
        for i, xval in enumerate(self.x_vals):
            x_item = QTableWidgetItem(str(xval))
            y_item = QTableWidgetItem(f"{self.predict_y(xval):.4f}")
            self.table.setItem(i, 0, x_item)
            self.table.setItem(i, 1, y_item)
        self.table.itemChanged.connect(self.update_table)

        # Análisis algebraico usando las utilidades
        analysis = analyze_polynomial_function(self.coef_, self.intercept_)
        analysis_text = f"<b>Dominio:</b> {analysis['Dominio']}<br>"
        analysis_text += f"<b>Rango:</b> {analysis['Rango']}<br>"
        analysis_text += f"<b>Puntos críticos:</b> {', '.join(f'({x:.4f}, {y:.4f})' for x, y in analysis['Puntos Críticos']) if analysis['Puntos Críticos'] else 'No hay'}<br>"
        analysis_text += f"<b>Ordenada al origen:</b> {analysis['Ordenada al Origen']:.4f}<br>"
        analysis_text += f"<b>Comportamiento:</b> {'; '.join(analysis['Comportamiento'])}"
        self.analysis_label.setText(analysis_text)
        self.analysis_text = analysis_text

    def predict_y(self, xval):
        """
        El método `predict_y` predice el valor de y para un x dado.
        : param xval: el valor de x para el que se desea predecir el valor de y
        : return: el método `predict_y` devuelve el valor de y predicho para el x dado
        """
        try:
            X_poly = self.poly.transform(np.array([[float(xval)]]))
            return self.model.predict(X_poly)[0]
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al predecir valor: {str(e)}")
            return 0

    def update_table(self, item):
        """
        El método `update_table` actualiza una tabla calculando y mostrando un valor y predicho basado en un valor x dado.
        : param item: El método `update_table` toma un `item` como parámetro. Este `item` se espera que sea
        un objeto QTableWidgetItem que representa una celda en una tabla. El método luego extrae la información de la fila y la columna
        de este elemento para realizar ciertas operaciones en la tabla
        """
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

    def plot_function(self):
        """
        El método `plot_function` gráfica una función ajustada y una función modificada si existe,
        basado en los datos y fórmulas proporcionados.
        : return: el método `plot_function` no devuelve nada explícitamente, ya que no tiene un` retorno`
        declaración al final de la función.
        """
        if self.x_col is None or self.y_col is None or self.model is None or self.poly is None:
            QMessageBox.warning(self, "Error", "Primero ajusta una función para poder graficar.")
            return
            
        try:
            # Usar datos según el checkbox
            x_plot_data, y_plot_data = self.data_for_plot
            x_plot = np.linspace(min(x_plot_data), max(x_plot_data), 200)
            
            plt.figure(figsize=(8, 5))
            
            # Graficar datos originales o agrupados
            if self.repeated_checkbox.isChecked():
                plt.scatter(x_plot_data, y_plot_data, color='blue', label='Datos sin repetir')
            else:
                plt.scatter(x_plot_data, y_plot_data, color='blue', label='Datos originales')
            
            # Graficar función ajustada
            X_plot_poly = self.poly.transform(x_plot.reshape(-1, 1))
            y_plot = self.model.predict(X_plot_poly)
            plt.plot(x_plot, y_plot, color='red', label='Función ajustada')
            
            # Graficar función modificada si existe
            modified_formula = self.formula_edit.text().strip()
            if modified_formula.replace(' ', '') == self.formula_edit.placeholderText().replace(' ', ''):
                y_modified = self.model.predict(self.poly.transform(x_plot.reshape(-1, 1)))
            else:
                # Si hay variables indefinidas, pedir valores al usuario
                undefined_in_formula = [v for v in self.undefined_vars if v in modified_formula]
                if undefined_in_formula:
                    values, ok = self.ask_for_undefined_vars(undefined_in_formula)
                    if not ok:
                        return
                    for v, val in values.items():
                        self.undefined_vars[v] = float(val)
                
                try:
                    y_modified = evaluate_modified_function(modified_formula, x_plot, self.undefined_vars)
                except ValueError as e:
                    QMessageBox.warning(self, "Error", str(e))
                    y_modified = self.model.predict(self.poly.transform(x_plot.reshape(-1, 1)))
            
            plt.plot(x_plot, y_modified, color='green', linestyle='--', label='Función modificada')
            plt.xlabel(self.x_col)
            plt.ylabel(self.y_col)
            plt.title(f'{self.y_col} vs {self.x_col}')
            plt.legend()
            plt.tight_layout()
            plt.show(block=False)
            
        except Exception as e:
            print(f"Error general al graficar: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al graficar: {str(e)}")

    def ask_for_undefined_vars(self, var_list):
        """
        El método `ask_for_undefined_vars` muestra un diálogo para que el usuario asigne valores a variables indefinidas.
        : param var_list: El método `ask_for_undefined_vars` toma un `var_list` como parámetro. Este `var_list` se espera que sea
        una lista de variables indefinidas. El método luego muestra un diálogo para que el usuario asigne valores a estas variables.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Asignar valores a variables indefinidas")
        layout = QFormLayout(dialog)
        edits = {}
        for var in var_list:
            edit = QLineEdit()
            edit.setPlaceholderText(f"Valor para {var}")
            layout.addRow(f"{var}", edit)
            edits[var] = edit
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dialog.setLayout(layout)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            values = {var: edits[var].text() for var in var_list}
            return values, True
        else:
            return {}, False

    def reset(self):
        self.formula_label.setText("")
        self.analysis_label.setText("")
        self.table.clear()
        self.ia_suggestion = None
        self.ia_suggestion_markdown = None

    def save_markdown(self):
        import re
        xvals = [self.table.item(i, 0).text() for i in range(self.table.rowCount())]
        yvals = [self.table.item(i, 1).text() for i in range(self.table.rowCount())]
        formula = self.formula_edit.text() if self.formula_edit.text().strip() else self.formula_label.text()
        # Guardar ambas funciones y análisis
        markdown = f"# Análisis de función entre columnas\n\n## Función ajustada\n\n$$\displaystyle {getattr(self, 'formula_ajustada_latex', '')}$$\n\n{getattr(self, 'analysis_text', '')}\n"
        if hasattr(self, 'ia_suggestion') and self.ia_suggestion:
            markdown += f"\n## Función sugerida por IA o modificada\n\n$$\displaystyle {formula}$$\n\n{getattr(self, 'analysis_ia_text', '')}\n"
        markdown += f"\n## Tabla de valores\n| {self.x_col} | {self.y_col} estimado |\n|---|---|\n" + "\n".join(f"| {x} | {y} |" for x, y in zip(xvals, yvals)) + f"\n"
        if self.ia_suggestion_markdown:
            markdown += f"\n{self.ia_suggestion_markdown}\n"
        if self.function_ajustada_explanation:
            markdown += f"\n{self.function_ajustada_explanation}\n"
        def safe_filename(s):
            return re.sub(r'[^a-zA-Z0-9_-]', '_', str(s))
        filename = f"Funcion_{safe_filename(self.x_col)}_vs_{safe_filename(self.y_col)}.md"
        with open(f"Análisis_de_datos/{filename}", "w", encoding="utf-8") as f:
            f.write(markdown)
        QMessageBox.information(self, "Guardado", f"El análisis se ha guardado en Análisis_de_datos/{filename}")

    def suggest_with_ia(self):
        """
        El método `suggest_with_ia` sugiere un modelo con IA.
        : return: el método `suggest_with_ia` no devuelve nada explícitamente, ya que no tiene un` retorno`
        declaración al final de la función.
        """
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
        """
        La clase `ModelSuggestion` en Python se utiliza para almacenar información sobre sugerencias de
        modelos matemáticos generadas por una IA, incluyendo el tipo de modelo, la fórmula sugerida y una
        explicación.
        """
        class ModelSuggestion(BaseModel):
            model_type: str
            formula: str
            explanation: str
            domain: str
            range: str
            critical_points: str
            y_intercept: str
            behavior: str
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
            f"f({x_col}) = ... \n -> f(firts_letter_of_x_col) = ...\n"
            f"X: {x}\n"
            f"Y: {y}\n  "
            "No use variables sin definir siempre define las variables basándote en los datos X, Y.\n"
            "Devuelve el análisis algebraico de la función sugerida en español, en los siguientes campos JSON: domain, range, critical_points, y_intercept, behavior.\n"
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
            # Mostrar la función sugerida por IA
            print(prompt)
            self.formula_label.setText(f"<b>Función sugerida por IA:</b> <br><pre>$$\displaystyle {suggestion.formula}$$</pre>")
            self.formula_edit.setText(suggestion.formula)
            # Mostrar el análisis algebraico de la IA
            analysis_ia_text = (
                f"<b>Dominio (IA):</b> {suggestion.domain}<br>"
                f"<b>Rango (IA):</b> {suggestion.range}<br>"
                f"<b>Puntos críticos (IA):</b> {suggestion.critical_points}<br>"
                f"<b>Ordenada al origen (IA):</b> {suggestion.y_intercept}<br>"
                f"<b>Comportamiento (IA):</b> {suggestion.behavior}"
            )
            self.analysis_label.setText(analysis_ia_text)
            self.analysis_ia_text = analysis_ia_text  # Guardar para Markdown
        except Exception as e:
            self.analysis_ia_text = "<b>Error al analizar la función sugerida por IA.</b>"
            QMessageBox.critical(self, "Error IA", f"Error al obtener sugerencia de IA: {str(e)}")

    def analyze_ajustada_with_ia(self):
        """
        El método `analyze_ajustada_with_ia` envía la función ajustada y los datos a la IA para que explique cada término de la función ajustada.
        : return: el método `analyze_ajustada_with_ia` no devuelve nada explícitamente, ya que no tiene un` retorno`
        declaración al final de la función.
        """
        x_col = self.x_col
        y_col = self.y_col
        x = self.df[x_col].values.tolist()
        y = self.df[y_col].values.tolist()
        formula = getattr(self, 'formula_ajustada_latex', self.formula_edit.text())
        # Prompt para la IA
        prompt = (
            f"Tengo una función ajustada por regresión polinómica entre dos variables de un conjunto de datos. "
            f"Variable independiente: {x_col}\n"
            f"Variable dependiente: {y_col}\n"
            f"Función ajustada: {formula}\n"
            f"X: {x}\n"
            f"Y: {y}\n"
            "Explica detalladamente el significado de cada término de la función ajustada en relación a los datos. "
            "Para cada coeficiente, explica a qué tendencia, patrón o característica de los datos corresponde. "
            "Redacta en español, de forma clara y didáctica, como si fuera para un informe técnico para no expertos. "
            "No inventes variables, usa solo las presentes en la función y los datos."
        )
        try:
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                QMessageBox.critical(self, "Error IA", "No se encontró GEMINI_API_KEY en el .env")
                return
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            explanation = response.text if hasattr(response, 'text') else str(response)
            # Guardar explicacion en markdown
            self.function_ajustada_explanation = explanation
            QMessageBox.information(self, "Markdown", f"Guarda la explicación en el archivo {self.x_col}_vs_{self.y_col}.md para poder verla en el explorador de archivos.")
        except Exception as e:
            QMessageBox.critical(self, "Error IA", f"Error al analizar la función ajustada con IA: {str(e)}") 