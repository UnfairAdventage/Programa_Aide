import matplotlib.pyplot as plt
import numpy as np

def plot_histogram(data, bins, class_marks=None, xlabel='Valor', ylabel='Frecuencia', title='Histograma de frecuencias'):
    plt.figure(figsize=(7,5))
    plt.hist(data, bins=bins, edgecolor='black', alpha=0.7)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    # Si se pasan marcas de clase, dibujar líneas y puntos rojizos
    if class_marks is not None:
        for mc in class_marks:
            plt.axvline(mc, color='crimson', linestyle='--', linewidth=2, alpha=0.7, label='Marca de clase' if mc == class_marks[0] else None)
            plt.plot(mc, 0, 'o', color='crimson')
        # Solo una vez en la leyenda
        handles, labels = plt.gca().get_legend_handles_labels()
        if 'Marca de clase' in labels:
            plt.legend()
    plt.tight_layout()
    plt.show()

def plot_frequency_polygon(class_marks, frequencies, xlabel='Marca de clase', ylabel='Frecuencia', title='Polígono de frecuencias'):
    # Cerrar el polígono al eje horizontal
    x = [class_marks[0] - (class_marks[1] - class_marks[0])] + list(class_marks) + [class_marks[-1] + (class_marks[1] - class_marks[0])]
    y = [0] + list(frequencies) + [0]
    plt.figure(figsize=(7,5))
    plt.plot(x, y, marker='o', linestyle='-', color='tab:blue')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

def plot_pie(frequencies, labels, title='Diagrama de pastel'):
    plt.figure(figsize=(6,6))
    plt.pie(frequencies, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.title(title)
    plt.tight_layout()
    plt.show() 