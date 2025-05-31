```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# Datos
grupos = ["A-B","C-D","E-F","G-H","I-J","K-L","M-N","O-P","Q-R","S-T","U-V","Y-Z"]
# Convertir grupos en valores numéricos (promedio de posiciones de letras)
letra_val = lambda l: ord(l) - ord('A') + 1
x = np.array([(letra_val(g[0]) + letra_val(g[2]))/2 for g in grupos]).reshape(-1, 1)
y = np.array([20, 9, 5, 1, 10, 8, 6, 4, 1, 4, 1, 1])

# Ajustar polinomios de grados 1 a 5 y calcular R²
results = []
for deg in range(1, 6):
    poly = PolynomialFeatures(degree=deg, include_bias=False)
    X_poly = poly.fit_transform(x)
    model = LinearRegression().fit(X_poly, y)
    y_pred = model.predict(X_poly)
    r2 = r2_score(y, y_pred)
    results.append({
        "Grado": deg,
        "R²": round(r2, 4),
        "Coeficientes": model.coef_.tolist(),
        "Intercepto": round(model.intercept_, 4)
    })

df_results = pd.DataFrame(results)
# Mostrar resultados
import ace_tools as tools; tools.display_dataframe_to_user(name="Resultados de Regresión Polinómica", dataframe=df_results)

# Seleccionar el mejor modelo (mayor R² sin sobreajuste excesivo, por ejemplo grado 3)
best = df_results.loc[df_results['Grado'] == 3].iloc[0]
coef = best["Coeficientes"]
intercept = best["Intercepto"]
# Construir fórmula
formula = f"f(x) = {coef[2]:.4f}x³ + {coef[1]:.4f}x² + {coef[0]:.4f}x + {intercept:.4f}"

#formula 'f(x) = -0.0047x³ + 0.2190x² + -3.3415x + 20.8532'
```