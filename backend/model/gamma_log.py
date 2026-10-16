import math

from backend.model.utils.lut import apply_lut


def build_gamma_lut(gamma):
    """Cria LUT da transformação gama normalizada."""
    if isinstance(gamma, bool) or not isinstance(gamma, (int, float)):
        raise TypeError("Gama deve ser um número.")

    if not math.isfinite(gamma) or gamma <= 0:
        raise ValueError("Gama deve ser positivo e finito.")

    lut = []
    for r in range(256):
        s = 255 * (r / 255) ** gamma
        lut.append(int(s + 0.5))

    return lut


def gamma_correction(matrix, gamma):
    """Aplica transformação de potência (gama) usando LUT."""
    lut = build_gamma_lut(gamma)
    return apply_lut(matrix, lut)


def build_log_lut():
    """Cria LUT da transformação logarítmica normalizada para 8 bits."""
    c = 255 / math.log(256)
    lut = []

    for r in range(256):
        s = c * math.log(1 + r)
        lut.append(int(s + 0.5))

    return lut


def log_transformation(matrix):
    """Aplica a transformação logarítmica usando LUT."""
    lut = build_log_lut()
    return apply_lut(matrix, lut)
