"""Negativo da imagem."""
import numpy as np

def negative_image(matrix: np.ndarray) -> np.ndarray:
    """Gera o negativo da imagem: s = (L - 1) - r.

    Recebe uma matriz 2D uint8 (altura, largura) e devolve uma nova
    matriz do mesmo formato, sem alterar a original.
    """
    if matrix.ndim != 2:
        raise ValueError("A imagem deve ser uma matriz 2D (escala de cinza).")

    height, width = matrix.shape
    negative = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            intensity = int(matrix[y, x])
            negative[y, x] = 255 - intensity

    return negative
