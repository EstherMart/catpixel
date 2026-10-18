"""Transformações geométricas: escala e rotação (com ou sem pivô), com interpolação.

As duas usam mapeamento inverso: para cada pixel da imagem de saída, calcula-se de onde ele veio na
imagem original (coordenadas reais) e a intensidade é estimada por interpolação. Isso não deixa
buracos na saída, o que aconteceria se cada pixel da entrada fosse empurrado para a saída.
Coordenadas são medidas no centro dos pixels: o primeiro pixel está em 0 e o último em largura - 1.
"""
import math

import numpy as np

NEAREST = "nearest"
BILINEAR = "bilinear"
METHODS = (NEAREST, BILINEAR)
MAX_OUTPUT_PIXELS = 40_000_000


def _check_method(method: str) -> None:
    if method not in METHODS:
        raise ValueError("O método de interpolação deve ser 'nearest' ou 'bilinear'.")


def _check_number(value, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"O valor de '{name}' deve ser um número finito.")


def _check_matrix(matrix: np.ndarray) -> None:
    if matrix.ndim != 2:
        raise ValueError("A imagem deve estar em escala de cinza.")


def _check_output_size(height: int, width: int) -> None:
    if height < 1 or width < 1:
        raise ValueError("O resultado ficaria com menos de 1 pixel de largura ou de altura.")
    if height * width > MAX_OUTPUT_PIXELS:
        raise ValueError("O resultado ficaria grande demais.")


def _sample(matrix: np.ndarray, xs: np.ndarray, ys: np.ndarray, method: str, clamp: bool) -> np.ndarray:
    """Estima a intensidade da imagem nas coordenadas reais (xs, ys).

    Pontos além da metade de um pixel fora da imagem ficam pretos, ou, com `clamp=True`, repetem a borda.
    """
    height, width = matrix.shape
    inside = (xs >= -0.5) & (xs < width - 0.5) & (ys >= -0.5) & (ys < height - 0.5)
    xs = np.clip(xs, 0, width - 1)
    ys = np.clip(ys, 0, height - 1)

    if method == NEAREST:
        values = matrix[np.floor(ys + 0.5).astype(int), np.floor(xs + 0.5).astype(int)]
    else:
        x0 = np.floor(xs).astype(int)
        y0 = np.floor(ys).astype(int)
        x1 = np.minimum(x0 + 1, width - 1)
        y1 = np.minimum(y0 + 1, height - 1)
        dx = xs - x0
        dy = ys - y0
        # média ponderada dos 4 vizinhos: v = (1-dx)(1-dy)·f00 + dx(1-dy)·f10 + (1-dx)dy·f01 + dx·dy·f11
        blended = (
            (1 - dx) * (1 - dy) * matrix[y0, x0]
            + dx * (1 - dy) * matrix[y0, x1]
            + (1 - dx) * dy * matrix[y1, x0]
            + dx * dy * matrix[y1, x1]
        )
        values = np.floor(blended + 0.5).astype(np.uint8)

    if not clamp:
        values = np.where(inside, values, 0).astype(np.uint8)
    return values


def scaled_shape(shape: tuple[int, int], scale_x: float, scale_y: float) -> tuple[int, int]:
    """(altura, largura) da imagem depois da escala."""
    _check_number(scale_x, "scale_x")
    _check_number(scale_y, "scale_y")
    if scale_x <= 0 or scale_y <= 0:
        raise ValueError("Os fatores de escala devem ser maiores que zero.")
    height, width = shape
    new_height, new_width = int(height * scale_y + 0.5), int(width * scale_x + 0.5)
    _check_output_size(new_height, new_width)
    return new_height, new_width


def scale_image(matrix: np.ndarray, scale_x: float, scale_y: float, method: str = BILINEAR) -> np.ndarray:
    """Amplia ou reduz a imagem: a largura é multiplicada por `scale_x` e a altura por `scale_y`."""
    _check_matrix(matrix)
    _check_method(method)
    new_height, new_width = scaled_shape(matrix.shape, scale_x, scale_y)

    # o centro do pixel de saída (i + 0.5)/escala, menos meio pixel, é a posição dele na imagem original
    xs = (np.arange(new_width) + 0.5) / (new_width / matrix.shape[1]) - 0.5
    ys = (np.arange(new_height) + 0.5) / (new_height / matrix.shape[0]) - 0.5
    grid_x, grid_y = np.meshgrid(xs, ys)
    return _sample(matrix, grid_x, grid_y, method, clamp=True)


def rotated_shape(shape: tuple[int, int], angle: float, expand: bool) -> tuple[int, int]:
    """(altura, largura) da imagem depois da rotação. Sem `expand`, o tamanho não muda."""
    _check_number(angle, "angle")
    height, width = shape
    if not expand:
        return height, width
    radians = math.radians(angle)
    cos, sin = abs(math.cos(radians)), abs(math.sin(radians))
    # o arredondamento a 9 casas evita que 90° (cos ≈ 6e-17) some um pixel a mais
    new_width = math.ceil(round(width * cos + height * sin, 9))
    new_height = math.ceil(round(width * sin + height * cos, 9))
    _check_output_size(new_height, new_width)
    return new_height, new_width


def rotate_image(
    matrix: np.ndarray,
    angle: float,
    method: str = BILINEAR,
    pivot: tuple[float, float] | None = None,
    expand: bool = False,
) -> np.ndarray:
    """Gira a imagem `angle` graus no sentido anti-horário (negativo gira no horário).

    - `pivot` é o ponto (x, y), em pixels, que fica parado. Sem ele, o centro da imagem é o pivô.
    - `expand=True` aumenta a tela para caber a imagem inteira. Não pode ser usado com `pivot`.
    - O que fica fora da imagem original vira preto.
    """
    _check_matrix(matrix)
    _check_method(method)
    if pivot is not None:
        _check_number(pivot[0], "pivot_x")
        _check_number(pivot[1], "pivot_y")
        if expand:
            raise ValueError("Não é possível aumentar a tela e girar em torno de um pivô ao mesmo tempo.")

    height, width = matrix.shape
    new_height, new_width = rotated_shape(matrix.shape, angle, expand)
    source_x, source_y = pivot if pivot is not None else ((width - 1) / 2, (height - 1) / 2)
    target_x, target_y = pivot if pivot is not None else ((new_width - 1) / 2, (new_height - 1) / 2)

    radians = math.radians(angle)
    cos, sin = math.cos(radians), math.sin(radians)
    grid_x, grid_y = np.meshgrid(np.arange(new_width) - target_x, np.arange(new_height) - target_y)
    # rotação inversa (de volta à imagem original), com y crescendo para baixo
    xs = source_x + grid_x * cos - grid_y * sin
    ys = source_y + grid_x * sin + grid_y * cos
    return _sample(matrix, xs, ys, method, clamp=False)
