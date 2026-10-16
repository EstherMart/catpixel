import numpy as np


def apply_lut(matrix, lut):
    """Aplica uma tabela de 256 intensidades a uma imagem 2D uint8."""
    if matrix.ndim != 2:
        raise ValueError("A imagem deve ser uma matriz 2D.")

    if matrix.dtype != np.uint8:
        raise TypeError("A imagem deve possuir dtype uint8.")

    if len(lut) != 256:
        raise ValueError("A LUT deve conter 256 valores.")

    if any(type(value) is not int or not 0 <= value <= 255 for value in lut):
        raise ValueError("A LUT deve conter inteiros entre 0 e 255.")

    height, width = matrix.shape
    result = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            intensity = int(matrix[y, x])
            result[y, x] = lut[intensity]

    return result
