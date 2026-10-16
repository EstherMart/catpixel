"""Convolução 2D com um filtro quadrado de dimensão ímpar (3x3, 5x5, 7x7, ...)."""
import math

import numpy as np

MAX_KERNEL_SIZE = 15
MAX_INTENSITY = 255


def validate_kernel(kernel) -> int:
    """Confere se o filtro é quadrado, de dimensão ímpar e só com números finitos. Devolve a dimensão."""
    size = len(kernel)
    if size % 2 == 0 or size > MAX_KERNEL_SIZE:
        raise ValueError(f"O filtro deve ter dimensão ímpar, de 1 a {MAX_KERNEL_SIZE}.")

    for row in kernel:
        if len(row) != size:
            raise ValueError("O filtro deve ser quadrado.")
        for value in row:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("Os valores do filtro devem ser números finitos.")

    return size


def convolve(matrix: np.ndarray, kernel, divisor: float = 1, normalize: bool = False) -> np.ndarray:
    """Convolui a imagem com o filtro e devolve uma imagem do mesmo tamanho.

    - Cada pixel vira a soma dos vizinhos multiplicados pelo filtro (girado 180°, como na convolução
      de verdade), dividida por `divisor`.
    - Nas bordas, o pixel mais próximo é repetido para fora da imagem.
    - O resultado pode sair de 0 a 255. Com `normalize=False` ele é cortado nesses limites. Com
      `normalize=True` o menor valor vira 0 e o maior vira 255 (útil para filtros de borda).
    """
    if matrix.ndim != 2:
        raise ValueError("A imagem deve estar em escala de cinza.")
    size = validate_kernel(kernel)
    if divisor == 0 or not math.isfinite(divisor):
        raise ValueError("O divisor deve ser um número finito e diferente de zero.")

    height, width = matrix.shape
    pad = size // 2
    padded = np.pad(matrix.astype(np.float64), pad, mode="edge")

    # Cada posição (i, j) do filtro soma, em todos os pixels de uma vez, a imagem deslocada
    # multiplicada pelo peso. É a mesma conta do laço pixel a pixel, só que em bloco.
    result = np.zeros((height, width), dtype=np.float64)
    for i in range(size):
        for j in range(size):
            weight = kernel[size - 1 - i][size - 1 - j]
            if weight != 0:
                result += weight * padded[i:i + height, j:j + width]
    result /= divisor

    lowest, highest = result.min(), result.max()
    if normalize and highest > lowest:
        result = (result - lowest) / (highest - lowest) * MAX_INTENSITY

    return np.floor(np.clip(result, 0, MAX_INTENSITY) + 0.5).astype(np.uint8)
