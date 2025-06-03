import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication, implicit_application
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from typing import Tuple, Dict, List, Optional, Union
import pandas as pd

def prepare_data(df: pd.DataFrame, x_col: str, y_col: str, use_repeated: bool = True) -> Tuple[np.ndarray, np.ndarray, Tuple[np.ndarray, np.ndarray]]:
    """
    Prepara los datos para el ajuste de función, manejando valores repetidos si es necesario.
    
    Args:
        df: DataFrame con los datos
        x_col: Nombre de la columna X
        y_col: Nombre de la columna Y
        use_repeated: Si True, usa promedio para valores repetidos
        
    Returns:
        Tuple con (x, y) para ajuste y (x_plot, y_plot) para graficar
    """
    if use_repeated:
        df_temp = df[[x_col, y_col]].copy()
        df_grouped = df_temp.groupby(x_col)[y_col].mean().reset_index()
        x = df_grouped[x_col].values.reshape(-1, 1)
        y = df_grouped[y_col].values
        plot_data = (x.flatten(), y)
    else:
        x = df[x_col].values.reshape(-1, 1)
        y = df[y_col].values
        plot_data = (x.flatten(), y)
    
    return x, y, plot_data

def fit_polynomial(x: np.ndarray, y: np.ndarray, degree: Optional[int] = None, auto_fit: bool = True) -> Dict:
    """
    Ajusta un polinomio a los datos, ya sea con grado fijo o automático.
    
    Args:
        x: Datos X
        y: Datos Y
        degree: Grado del polinomio (si auto_fit es False)
        auto_fit: Si True, encuentra el mejor grado automáticamente
        
    Returns:
        Diccionario con el modelo ajustado y sus parámetros
    """
    if auto_fit:
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
    else:
        poly = PolynomialFeatures(degree=degree, include_bias=False)
        X_poly = poly.fit_transform(x)
        model = LinearRegression().fit(X_poly, y)
        y_pred = model.predict(X_poly)
        best_r2 = r2_score(y, y_pred)
        best_deg = degree
        best_model = model
        best_poly = poly
    
    return {
        'model': best_model,
        'poly': best_poly,
        'degree': best_deg,
        'r2': best_r2,
        'coef': best_model.coef_.tolist(),
        'intercept': best_model.intercept_
    }

def format_polynomial_formula(coef: List[float], intercept: float) -> Tuple[str, Dict[str, float]]:
    """
    Formatea la fórmula del polinomio, manejando variables indefinidas.
    
    Args:
        coef: Lista de coeficientes
        intercept: Término independiente
        
    Returns:
        Tuple con la fórmula en formato LaTeX y diccionario de variables indefinidas
    """
    terms = []
    undefined_vars = {}
    
    for i in range(len(coef)-1, -1, -1):
        coef_val = coef[i]
        if abs(coef_val) < 1e-10:
            var_name = f"a_{i+1}"
            undefined_vars[var_name] = coef_val
            terms.append(f"{var_name}x^{i+1}")
        else:
            terms.append(f"{coef_val:+.4f}x^{i+1}")
    
    formula = f"f(x) = {' '.join(terms)} {intercept:+.4f}"
    return formula, undefined_vars

def evaluate_modified_function(formula: str, x: np.ndarray, undefined_vars: Dict[str, float]) -> np.ndarray:
    """
    Evalúa una función modificada con variables indefinidas.
    
    Args:
        formula: Fórmula de la función
        x: Valores de x para evaluar
        undefined_vars: Diccionario con valores de variables indefinidas
        
    Returns:
        Array con los valores evaluados
    """
    import re
    
    # Limpiar la fórmula
    formula = re.sub(r'^(f\(x\)|y)\s*=\s*', '', formula, flags=re.IGNORECASE)
    formula = formula.replace('^', '**')
    formula = formula.replace(',', '.')
    formula = formula.replace(' ', '')
    
    # Crear símbolos
    x_sym = sp.Symbol('x')
    symbols = {'x': x_sym}
    for var_name, value in undefined_vars.items():
        symbols[var_name] = sp.Symbol(var_name)
    
    # Parsear y evaluar
    transformations = (
        standard_transformations + 
        (implicit_multiplication, implicit_application)
    )
    
    try:
        expr = parse_expr(
            formula,
            transformations=transformations,
            local_dict=symbols
        )
        expr = sp.simplify(expr)
        f = sp.lambdify(x_sym, expr, 'numpy')
        return f(x)
    except Exception as e:
        raise ValueError(f"Error al evaluar la función: {str(e)}")

def analyze_polynomial_function(coef: List[float], intercept: float) -> Dict:
    """
    Analiza una función polinómica, encontrando dominio, rango, puntos críticos, etc.
    
    Args:
        coef: Lista de coeficientes
        intercept: Término independiente
        
    Returns:
        Diccionario con el análisis de la función
    """
    # Crear símbolo x
    x = sp.Symbol('x')
    
    # Construir la expresión
    expr = intercept
    for i, c in enumerate(coef):
        expr += c * x**(i+1)
    
    # Derivada
    deriv = sp.diff(expr, x)
    
    # Puntos críticos
    critical_points = []
    if len(coef) > 1:  # Solo si es polinomio de grado > 1
        solutions = sp.solve(deriv, x)
        for sol in solutions:
            if sol.is_real:
                y_val = expr.subs(x, sol)
                critical_points.append((float(sol), float(y_val)))
    
    # Comportamiento
    behavior = []
    if len(coef) > 0:
        if coef[-1] > 0:
            behavior.append("La función crece sin límite cuando x → ∞")
        else:
            behavior.append("La función decrece sin límite cuando x → ∞")
        
        if len(coef) % 2 == 0:
            if coef[-1] > 0:
                behavior.append("La función decrece sin límite cuando x → -∞")
            else:
                behavior.append("La función crece sin límite cuando x → -∞")
        else:
            if coef[-1] > 0:
                behavior.append("La función crece sin límite cuando x → -∞")
            else:
                behavior.append("La función decrece sin límite cuando x → -∞")
    
    if intercept != 0:
        behavior.append(f"La función se desplaza {abs(intercept):.4f} unidades hacia {'arriba' if intercept > 0 else 'abajo'}")
    
    return {
        'Dominio': 'ℝ (todos los números reales)',
        'Rango': 'ℝ (todos los números reales)',
        'Puntos Críticos': critical_points,
        'Ordenada al Origen': float(intercept),
        'Comportamiento': behavior
    } 