from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt
from src.utils.data_grouping import group_by_initial, group_by_frequency, group_by_similarity, get_grouping_recommendation
import difflib
from collections import Counter

class QualitativeGroupingDialog(QDialog):
    def __init__(self, series, column_name, recommendation=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Agrupación de '{column_name}'")
        self.setMinimumSize(700, 600)
        self.series = series.astype(str)
        self.column_name = column_name
        self.unique_values = sorted(self.series.unique())
        self.mapping = {val: val for val in self.unique_values}
        self.recommendation = recommendation or get_grouping_recommendation(self.series)

        layout = QVBoxLayout(self)

        # Tooltip explicativo
        tooltip = (
            "<b>¿Cómo agrupar?</b><br>"
            "- Puedes editar el nombre del grupo en la columna 'Grupo'.<br>"
            "- Selecciona varias filas (Ctrl+clic o Shift+clic) y usa el campo y botón para asignar el mismo grupo.<br>"
            "- Ejemplos: <br>"
            "&nbsp;&nbsp;• <i>Salud</i>: Médico, Enfermero<br>"
            "&nbsp;&nbsp;• <i>Alta frecuencia</i>: productos más vendidos<br>"
            "&nbsp;&nbsp;• <i>Rojo</i>: rojo, rojizo, colorado<br>"
            "- Puedes usar los métodos automáticos y luego ajustar manualmente."
        )
        help_label = QLabel()
        help_label.setTextFormat(Qt.TextFormat.RichText)
        help_label.setText(tooltip)
        layout.addWidget(help_label)

        # Recomendación
        rec_label = QLabel(f"Recomendación: <b>{self.recommendation.capitalize()}</b>")
        layout.addWidget(rec_label)

        # Métodos y explicaciones
        self.method_explanations = {
            "Manual": "Edita los grupos uno a uno o en bloque. Útil para agrupaciones personalizadas o semánticas.",
            "Por Inicial": "Agrupa por la letra inicial (o pares de iniciales) de cada valor. Útil para muchas categorías.",
            "Por Frecuencia": "Agrupa en Alta, Media y Baja frecuencia según la ocurrencia de cada valor.",
            "Por Similitud (básico)": "Agrupa valores similares fonéticamente o por sinónimos. Ejemplo: 'rojo', 'rojizo', 'colorado' → Rojo.",
            "Por Categoría Jerárquica (conceptual)": "Agrupa valores en categorías amplias definidas por el usuario. Ejemplo: Profesión → Salud, Tecnología, Educación, Legal.",
            "Por Geografía/Cultura/Política": "Agrupa por regiones, continentes, bloques económicos, etc. Ejemplo: País → América Latina, Europa Occidental...",
            "Por Binarización/Dicotomía": "Agrupa en dos grandes grupos (Sí/No, Alto/Bajo, Manual/No manual, etc.).",
            "Por Codificación Ordinal": "Asigna un orden lógico a las categorías (ej: Primaria < Secundaria < Universidad).",
            "Por Clustering/Estadístico": "Agrupa automáticamente usando análisis estadístico (clustering, K-Means, etc.) si hay datos asociados."
        }

        # Selector de método
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Método de agrupación:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(list(self.method_explanations.keys()))
        self.method_combo.setCurrentText(self._method_from_recommendation())
        self.method_combo.currentTextChanged.connect(self.apply_method)
        self.method_combo.currentTextChanged.connect(self.update_method_explanation)
        method_layout.addWidget(self.method_combo)
        layout.addLayout(method_layout)

        # Explicación dinámica del método
        self.method_explanation_label = QLabel()
        self.method_explanation_label.setWordWrap(True)
        self.method_explanation_label.setText(self.method_explanations[self.method_combo.currentText()])
        layout.addWidget(self.method_explanation_label)

        # Tabla editable valor original -> grupo
        self.table = QTableWidget(len(self.unique_values), 2)
        self.table.setHorizontalHeaderLabels(["Valor original", "Grupo"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for i, val in enumerate(self.unique_values):
            self.table.setItem(i, 0, QTableWidgetItem(val))
            self.table.setItem(i, 1, QTableWidgetItem(val))
        layout.addWidget(self.table)

        # Campo y botón para asignar grupo a selección
        assign_layout = QHBoxLayout()
        assign_layout.addWidget(QLabel("Asignar grupo a selección:"))
        self.group_lineedit = QLineEdit()
        assign_layout.addWidget(self.group_lineedit)
        assign_btn = QPushButton("Asignar")
        assign_btn.clicked.connect(self.assign_group_to_selection)
        assign_layout.addWidget(assign_btn)
        layout.addLayout(assign_layout)

        # Botones
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("Aceptar")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        # Aplicar método recomendado al inicio
        self.apply_method(self.method_combo.currentText())

    def _method_from_recommendation(self):
        rec = self.recommendation.lower()
        if rec == "inicial":
            return "Por Inicial"
        if rec == "frecuencia":
            return "Por Frecuencia"
        if rec == "manual":
            return "Manual"
        if rec == "similitud":
            return "Por Similitud (básico)"
        return "Manual"

    def update_method_explanation(self, method):
        self.method_explanation_label.setText(self.method_explanations.get(method, ""))

    def apply_method(self, method):
        if method == "Manual":
            for i, val in enumerate(self.unique_values):
                self.table.setItem(i, 1, QTableWidgetItem(val))
        elif method == "Por Inicial":
            grouped = group_by_initial(self.series)
            for i, val in enumerate(self.unique_values):
                self.table.setItem(i, 1, QTableWidgetItem(grouped[self.series == val].iloc[0]))
        elif method == "Por Frecuencia":
            grouped = group_by_frequency(self.series)
            for i, val in enumerate(self.unique_values):
                self.table.setItem(i, 1, QTableWidgetItem(grouped[self.series == val].iloc[0]))
        elif method == "Por Similitud (básico)":
            # Agrupa valores similares usando difflib
            groups = []
            used = set()
            for val in self.unique_values:
                if val in used:
                    continue
                similars = [v for v in self.unique_values if difflib.SequenceMatcher(None, val.lower(), v.lower()).ratio() > 0.8]
                for s in similars:
                    used.add(s)
                groups.append(similars)
            group_names = [g[0] for g in groups]
            val_to_group = {}
            for group, name in zip(groups, group_names):
                for v in group:
                    val_to_group[v] = name
            for i, val in enumerate(self.unique_values):
                self.table.setItem(i, 1, QTableWidgetItem(val_to_group[val]))
        elif method == "Por Categoría Jerárquica (conceptual)":
            # Palabras clave básicas para ejemplo
            categorias = {
                'Salud': ['médico', 'enfermero', 'doctor', 'enfermera'],
                'Tecnología': ['ingeniero', 'programador', 'desarrollador', 'sistemas'],
                'Educación': ['profesor', 'maestro', 'docente'],
                'Legal': ['abogado', 'juez', 'fiscal']
            }
            def get_cat(val):
                for cat, palabras in categorias.items():
                    for p in palabras:
                        if p in val.lower():
                            return cat
                return '(Definir categoría)'
            for i, val in enumerate(self.unique_values):
                self.table.setItem(i, 1, QTableWidgetItem(get_cat(val)))
        elif method == "Por Geografía/Cultura/Política":
            # Listas básicas de países/regiones
            latam = ['méxico', 'argentina', 'chile', 'perú', 'colombia', 'brasil', 'uruguay', 'paraguay', 'bolivia', 'ecuador', 'venezuela', 'cuba', 'guatemala', 'honduras', 'el salvador', 'nicaragua', 'costa rica', 'panamá', 'puerto rico', 'república dominicana']
            europa = ['francia', 'alemania', 'españa', 'italia', 'portugal', 'reino unido', 'suiza', 'bélgica', 'países bajos', 'suecia', 'noruega', 'dinamarca', 'finlandia', 'austria', 'irlanda']
            def get_region(val):
                v = val.lower()
                if any(p in v for p in latam):
                    return 'América Latina'
                if any(p in v for p in europa):
                    return 'Europa Occidental'
                return '(Definir región)'
            for i, val in enumerate(self.unique_values):
                self.table.setItem(i, 1, QTableWidgetItem(get_region(val)))
        elif method == "Por Binarización/Dicotomía":
            # Dos valores más frecuentes
            counts = Counter(self.series)
            comunes = [v for v, _ in counts.most_common(2)]
            for i, val in enumerate(self.unique_values):
                if val == comunes[0]:
                    self.table.setItem(i, 1, QTableWidgetItem('Grupo 1'))
                elif len(comunes) > 1 and val == comunes[1]:
                    self.table.setItem(i, 1, QTableWidgetItem('Grupo 2'))
                else:
                    self.table.setItem(i, 1, QTableWidgetItem('Otro'))
        elif method == "Por Codificación Ordinal":
            # Orden alfabético
            for i, val in enumerate(self.unique_values):
                self.table.setItem(i, 1, QTableWidgetItem(f"{i+1}: {val}"))
        elif method == "Por Clustering/Estadístico":
            # Si hay datos numéricos asociados, usar KMeans (placeholder)
            try:
                from sklearn.cluster import KMeans
                import numpy as np
                # Buscar si hay una columna numérica asociada
                # (En este ejemplo, solo placeholder: asigna clusters por frecuencia)
                freq = Counter(self.series)
                vals = np.array([[freq[v]] for v in self.unique_values])
                n_clusters = min(3, len(self.unique_values))
                kmeans = KMeans(n_clusters=n_clusters, n_init=10)
                labels = kmeans.fit_predict(vals)
                for i, val in enumerate(self.unique_values):
                    self.table.setItem(i, 1, QTableWidgetItem(f"Cluster {labels[i]+1}"))
            except Exception:
                # Si no hay sklearn, asignar clusters por frecuencia
                for i, val in enumerate(self.unique_values):
                    self.table.setItem(i, 1, QTableWidgetItem(f"Cluster {1 + (i % 3)}"))

    def assign_group_to_selection(self):
        group_name = self.group_lineedit.text().strip()
        if not group_name:
            QMessageBox.warning(self, "Error", "Debes ingresar un nombre de grupo.")
            return
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Error", "Selecciona al menos una fila.")
            return
        for idx in selected:
            self.table.setItem(idx.row(), 1, QTableWidgetItem(group_name))

    def get_mapping(self):
        mapping = {}
        for i, val in enumerate(self.unique_values):
            group = self.table.item(i, 1).text() if self.table.item(i, 1) else val
            mapping[val] = group
        return mapping 