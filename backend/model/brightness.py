import math
import numpy as np

from backend.model.utils.lut import apply_lut


def build_brightness_lut(brightness):
    """Cria LUT de brilho multiplicativo: s = clip(r * brightness, 0, 255)."""
    if isinstance(brightness, bool) or not isinstance(brightness, (int, float)):
        raise TypeError("O fator de brilho deve ser um número.")

    if not math.isfinite(brightness) or brightness < 0:
        raise ValueError("O fator de brilho deve ser finito e não negativo.")

    lut = []

    for r in range(256):
        s = r * brightness
        s = max(0, min(255, s))
        lut.append(int(s + 0.5))

    return lut


def adjust_brightness(matrix, brightness):
    """Ajusta o brilho da imagem sem alterar a matriz original."""
    lut = build_brightness_lut(brightness)
    return apply_lut(matrix, lut)


def mean_brightness(matrix):
    """Calcula a média dos valores de intensidade (não o brilho percebido)."""
    if matrix.ndim != 2:
        raise ValueError("A imagem deve ser uma matriz 2D.")

    if matrix.dtype != np.uint8:
        raise TypeError("A imagem deve possuir dtype uint8.")

    height, width = matrix.shape
    if height == 0 or width == 0:
        raise ValueError("A imagem não pode estar vazia.")

    total = 0
    for y in range(height):
        for x in range(width):
            total += int(matrix[y, x])

    return total / (height * width)
