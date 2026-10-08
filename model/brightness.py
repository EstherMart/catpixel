import numpy as np
import math

def build_brightness_lut(brightness):
    """
    Soma com clipping: s = clip(r + brightness).
    """

    if not isinstance(brightness, int):
        raise TypeError("O brilho deve ser um número inteiro.")

    if not -255 <= brightness <= 255:
        raise ValueError("O brilho deve estar entre -255 e 255.")
    
    lut = []
    for r in range(256):
        s = r + brightness
        lut.append(max(0, min(255, s)))
    return lut


def build_gamma_lut(gamma):
    """
    Gama normalizada: s = 255 * (r / 255) ** gamma.
    """
    if not math.isfinite(gamma) or gamma <= 0:
        raise ValueError("Gama deve ser positivo e finito.")
    
    return [int(255 * (r / 255) ** gamma + 0.5) for r in range(256)]


def build_log_lut():
    """
    Transformação logarítmica normalizada.
    """
    c = 255 / math.log(256)

    lut = []

    for r in range(256):
        s = c * math.log(1 + r)
        lut.append(int(s + 0.5))

    return lut

def mean_brightness(matrix):
    """
    Calcula a intensidade média de uma imagem em escala de cinza.
    """
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

def apply_lut(matrix, lut):
    """
    Aplica uma LUT a uma imagem uint8 em escala de cinza.
    """
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
