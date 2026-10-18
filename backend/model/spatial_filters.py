"""Filtros espaciais: suavização (média, gaussiana, mediana) e aguçamento (Laplaciano e high-boost).

As definições seguem o Capítulo 3 do livro-texto (seções 3.5 e 3.6). Os filtros lineares usam
`convolve_raw`, e a mediana, que não é linear, é calculada aqui.
"""
import numpy as np

from backend.model.convolution import (
    clip_to_uint8,
    convolve_raw,
    normalize_for_display,
    validate_size,
)

# Laplaciano com centro negativo (Figura 3.37 a, b): g = f + c·∇²f com c = -1.
LAPLACIAN_4 = [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
LAPLACIAN_8 = [[1, 1, 1], [1, -8, 1], [1, 1, 1]]

MEDIAN_BAND_ROWS = 64  # a mediana empilha todas as vizinhanças; em faixas de linhas, a memória fica limitada


def mean_kernel(size: int):
    """Filtro da média: todos os pesos 1, com divisor size²."""
    validate_size(size)
    return [[1] * size for _ in range(size)], size * size


def gaussian_kernel(size: int):
    """Média ponderada: pesos binomiais (linha do triângulo de Pascal) em duas dimensões, que aproximam a gaussiana."""
    validate_size(size)
    row = [1]
    for _ in range(size - 1):
        row = [a + b for a, b in zip([0] + row, row + [0])]
    total = sum(row)
    return [[a * b for b in row] for a in row], total * total


def mean_filter(matrix: np.ndarray, size: int) -> np.ndarray:
    kernel, divisor = mean_kernel(size)
    return clip_to_uint8(convolve_raw(matrix, kernel, divisor))


def gaussian_filter(matrix: np.ndarray, size: int) -> np.ndarray:
    kernel, divisor = gaussian_kernel(size)
    return clip_to_uint8(convolve_raw(matrix, kernel, divisor))


def median_filter(matrix: np.ndarray, size: int) -> np.ndarray:
    """Cada pixel vira a mediana das intensidades da vizinhança size × size (ele mesmo incluído)."""
    if matrix.ndim != 2:
        raise ValueError("A imagem deve estar em escala de cinza.")
    validate_size(size)

    height, width = matrix.shape
    pad = size // 2
    padded = np.pad(matrix, pad, mode="edge")
    result = np.zeros((height, width), dtype=np.uint8)

    for top in range(0, height, MEDIAN_BAND_ROWS):
        bottom = min(top + MEDIAN_BAND_ROWS, height)
        # uma camada por posição da vizinhança; ordenar as camadas e pegar a do meio dá a mediana
        layers = [padded[top + i:bottom + i, j:j + width] for i in range(size) for j in range(size)]
        result[top:bottom] = np.sort(np.stack(layers), axis=0)[len(layers) // 2]

    return result


def laplacian_filter(matrix: np.ndarray, diagonals: bool = False, sharpen: bool = True) -> np.ndarray:
    """Laplaciano da imagem.

    - `sharpen=True`: aguçamento g = f - ∇²f (equação 3.6-7 com c = -1), cortado em 0 a 255.
    - `sharpen=False`: só o laplaciano, ajustado para exibição (menor valor em 0, maior em 255).
    - `diagonals=True` usa a máscara com os 8 vizinhos, que realça também as bordas diagonais.
    """
    laplacian = convolve_raw(matrix, LAPLACIAN_8 if diagonals else LAPLACIAN_4)
    if not sharpen:
        return normalize_for_display(laplacian)
    return clip_to_uint8(matrix.astype(np.float64) - laplacian)


def high_boost_filter(matrix: np.ndarray, size: int, k: float, gaussian: bool = False) -> np.ndarray:
    """Máscara de nitidez e high-boost: g = f + k·(f - f_suavizada).

    Com k = 1 é a máscara de nitidez (unsharp masking), com k > 1 é high-boost e com k < 1 o efeito diminui.
    """
    if k < 0:
        raise ValueError("O peso k deve ser maior ou igual a zero.")
    kernel, divisor = gaussian_kernel(size) if gaussian else mean_kernel(size)
    blurred = convolve_raw(matrix, kernel, divisor)
    original = matrix.astype(np.float64)
    return clip_to_uint8(original + k * (original - blurred))
