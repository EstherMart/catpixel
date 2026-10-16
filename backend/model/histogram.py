"""Histograma de intensidades e equalização de histograma."""
import numpy as np

from backend.model.utils.lut import apply_lut

LEVELS = 256


def compute_histogram(matrix: np.ndarray) -> list[int]:
    """Conta quantos pixels existem em cada intensidade (0 a 255)."""
    if matrix.ndim != 2:
        raise ValueError("A imagem deve estar em escala de cinza.")

    counts = [0] * LEVELS
    height, width = matrix.shape
    for y in range(height):
        for x in range(width):
            counts[int(matrix[y, x])] += 1

    return counts


def build_equalization_lut(counts: list[int]) -> list[int]:
    """LUT da equalização: s = round((cdf(r) - cdf_min) / (N - cdf_min) · 255).

    `cdf` é a soma acumulada do histograma e `cdf_min` é o primeiro valor não nulo dela.
    """
    total = sum(counts)

    cdf = []
    running = 0
    for count in counts:
        running += count
        cdf.append(running)

    cdf_min = next((value for value in cdf if value > 0), 0)
    if total == cdf_min:  # um único tom na imagem: não há o que equalizar
        return list(range(LEVELS))

    return [int((value - cdf_min) / (total - cdf_min) * (LEVELS - 1) + 0.5) if value > cdf_min else 0
            for value in cdf]


def equalize_histogram(matrix: np.ndarray) -> np.ndarray:
    """Espalha as intensidades pelo intervalo completo, aumentando o contraste."""
    lut = build_equalization_lut(compute_histogram(matrix))
    return apply_lut(matrix, lut)
