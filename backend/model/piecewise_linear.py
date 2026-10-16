"""Transformação linear definida por partes (alongamento de contraste) por tabela de consulta (LUT)."""
from backend.model.utils.lut import apply_lut

MAX_INTENSITY = 255


def build_piecewise_lut(points):
    """Cria a LUT que liga, em linha reta, os pontos (r, s) dados.

    O gráfico sempre passa por (0, 0) e (255, 255); `points` traz os pontos do meio.
    Pontos fora de ordem são ordenados por r. Dois pontos com o mesmo r formam um degrau.
    """
    for r, s in points:
        if not (0 <= r <= MAX_INTENSITY and 0 <= s <= MAX_INTENSITY):
            raise ValueError("Os pontos devem ter valores entre 0 e 255.")

    vertices = [(0, 0), *sorted(points), (MAX_INTENSITY, MAX_INTENSITY)]

    lut = []
    for r in range(MAX_INTENSITY + 1):
        s = r
        for (r0, s0), (r1, s1) in zip(vertices, vertices[1:]):
            if r0 <= r <= r1 and r1 > r0:  # r1 == r0 é um degrau: não tem inclinação
                s = s0 + (s1 - s0) * (r - r0) / (r1 - r0)
                break
        lut.append(int(s + 0.5))

    return lut


def piecewise_linear(matrix, r1, s1, r2, s2):
    """Aplica a função linear por partes (0,0) → (r1,s1) → (r2,s2) → (255,255)."""
    lut = build_piecewise_lut([(r1, s1), (r2, s2)])
    return apply_lut(matrix, lut)
