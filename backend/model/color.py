"""Imagens coloridas: conversão RGB <-> HSI, escala de cinza, ajustes de cor, sépia e chroma-key.

Uma imagem colorida é uma matriz uint8 (altura, largura, 3) na ordem R, G, B. As fórmulas de conversão
seguem o Capítulo 6 do livro-texto (equações 6.2-2 a 6.2-7), e a equalização, a seção 6.5.5.
"""

import numpy as np

from backend.model.convolution import clip_to_uint8
from backend.model.geometry import BILINEAR, resize_image
from backend.model.histogram import build_equalization_lut, compute_histogram
from backend.model.utils.lut import apply_lut

GRAY_WEIGHTS = (0.299, 0.587, 0.114)  # média ponderada: o olho vê o verde mais claro que o azul
SEPIA_MATRIX = np.array([[0.393, 0.769, 0.189], [0.349, 0.686, 0.168], [0.272, 0.534, 0.131]])
HSI_COMPONENTS = ("hue", "saturation", "intensity")
MAX_KEY_DISTANCE = 442  # distância máxima entre duas cores RGB: raiz de 3 · 255²


def _check_color(matrix: np.ndarray) -> None:
    if matrix.ndim != 3 or matrix.shape[2] != 3 or matrix.dtype != np.uint8:
        raise ValueError("A imagem deve ser colorida (altura, largura, 3) com valores de 0 a 255.")


def as_color(matrix: np.ndarray) -> np.ndarray:
    """Uma imagem em cinza vira colorida com R = G = B. Uma colorida volta como está."""
    if matrix.ndim == 2:
        return np.stack([matrix] * 3, axis=-1)
    _check_color(matrix)
    return matrix


def intensity(matrix: np.ndarray) -> np.ndarray:
    """Intensidade I = (R + G + B) / 3, arredondada. Numa imagem em cinza, é a própria imagem."""
    if matrix.ndim == 2:
        return matrix
    _check_color(matrix)
    return np.floor(matrix.astype(np.float64).sum(axis=2) / 3 + 0.5).astype(np.uint8)


# ---------- escala de cinza ----------

def to_grayscale(matrix: np.ndarray, weighted: bool = False) -> np.ndarray:
    """Converte para cinza pela média simples (R+G+B)/3 ou pela média ponderada 0,299R + 0,587G + 0,114B."""
    if matrix.ndim == 2:
        return matrix.copy()
    _check_color(matrix)
    if not weighted:
        return intensity(matrix)
    values = matrix.astype(np.float64) @ np.array(GRAY_WEIGHTS)
    return clip_to_uint8(values)


# ---------- RGB <-> HSI ----------

def rgb_to_hsi(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Converte RGB (0 a 255) em H (graus, 0 a 360), S (0 a 1) e I (0 a 1), pixel a pixel.

    I = (R+G+B)/3;  S = 1 − 3·min(R,G,B)/(R+G+B);  H = θ se B ≤ G, senão 360° − θ, com
    θ = cos⁻¹( ½[(R−G)+(R−B)] / √[(R−G)² + (R−B)(G−B)] ).
    Em cinza (R = G = B) o matiz não existe e fica 0, e S = 0.
    """
    _check_color(matrix)
    red, green, blue = (matrix[:, :, channel].astype(np.float64) / 255 for channel in range(3))

    intensity_ = (red + green + blue) / 3
    lowest = np.minimum(np.minimum(red, green), blue)
    saturation = np.zeros_like(intensity_)
    np.divide(lowest, intensity_, out=saturation, where=intensity_ > 0)
    saturation = 1 - saturation  # 1 - 3·min/(R+G+B) = 1 - min/I
    saturation[intensity_ == 0] = 0

    numerator = 0.5 * ((red - green) + (red - blue))
    denominator = np.sqrt((red - green) ** 2 + (red - blue) * (green - blue))
    ratio = np.zeros_like(intensity_)
    np.divide(numerator, denominator, out=ratio, where=denominator > 1e-12)
    theta = np.degrees(np.arccos(np.clip(ratio, -1, 1)))  # o clip evita erro de arredondamento fora de [-1, 1]
    hue = np.where(blue <= green, theta, 360 - theta)
    hue[denominator <= 1e-12] = 0
    return hue, saturation, intensity_


def hsi_to_rgb(hue: np.ndarray, saturation: np.ndarray, intensity_: np.ndarray) -> np.ndarray:
    """Converte H (graus), S e I (0 a 1) de volta para RGB (equações 6.2-5 a 6.2-7, por setor de 120°)."""
    hue = np.mod(hue, 360)  # o matiz dá a volta: 370° é o mesmo que 10°
    saturation = np.clip(saturation, 0, 1)
    intensity_ = np.clip(intensity_, 0, 1)

    red = np.zeros_like(hue)
    green = np.zeros_like(hue)
    blue = np.zeros_like(hue)

    for sector, start in enumerate((0, 120, 240)):
        inside = (hue >= start) & (hue < start + 120)
        angle = (hue - start)[inside]
        i, s = intensity_[inside], saturation[inside]
        low = i * (1 - s)  # o componente "oposto" ao setor
        high = i * (1 + s * np.cos(np.radians(angle)) / np.cos(np.radians(60 - angle)))
        rest = 3 * i - (low + high)
        if sector == 0:  # setor RG
            blue[inside], red[inside], green[inside] = low, high, rest
        elif sector == 1:  # setor GB
            red[inside], green[inside], blue[inside] = low, high, rest
        else:  # setor BR
            green[inside], blue[inside], red[inside] = low, high, rest

    rgb = np.stack([red, green, blue], axis=-1)
    return clip_to_uint8(rgb * 255)


def hsi_component(matrix: np.ndarray, component: str) -> np.ndarray:
    """Mostra um componente HSI como imagem em cinza: H em graus (0 a 360 vira 0 a 255), S e I de 0 a 1 (vira 0 a 255)."""
    if component not in HSI_COMPONENTS:
        raise ValueError("O componente deve ser 'hue', 'saturation' ou 'intensity'.")
    hue, saturation, intensity_ = rgb_to_hsi(as_color(matrix))
    values = {"hue": hue / 360, "saturation": saturation, "intensity": intensity_}[component]
    return clip_to_uint8(values * 255)


def adjust_hsi(matrix: np.ndarray, hue_shift: float, saturation_factor: float, intensity_factor: float) -> np.ndarray:
    """Soma `hue_shift` graus ao matiz e multiplica a saturação e a intensidade pelos fatores (cortando em 1)."""
    if saturation_factor < 0 or intensity_factor < 0:
        raise ValueError("Os fatores de saturação e de brilho não podem ser negativos.")
    hue, saturation, intensity_ = rgb_to_hsi(as_color(matrix))
    return hsi_to_rgb(hue + hue_shift, saturation * saturation_factor, intensity_ * intensity_factor)


def equalize_intensity(matrix: np.ndarray) -> np.ndarray:
    """Equalização de histograma em imagem colorida: só o componente I é equalizado, e H e S ficam como estão.

    Equalizar R, G e B separadamente mudaria as cores. No modelo HSI, a cor (H e S) fica separada do brilho (I).
    """
    hue, saturation, intensity_ = rgb_to_hsi(as_color(matrix))
    levels = clip_to_uint8(intensity_ * 255)
    lut = build_equalization_lut(compute_histogram(levels))
    return hsi_to_rgb(hue, saturation, apply_lut(levels, lut) / 255)


# ---------- histogramas ----------

def channel_histograms(matrix: np.ndarray) -> dict[str, list[int]]:
    """Histogramas de uma imagem: só 'i' em cinza, ou 'r', 'g', 'b' e 'i' (intensidade) em colorida."""
    if matrix.ndim == 2:
        return {"i": compute_histogram(matrix)}
    _check_color(matrix)
    counts = {name: compute_histogram(matrix[:, :, channel]) for channel, name in enumerate("rgb")}
    counts["i"] = compute_histogram(intensity(matrix))
    return counts


# ---------- ajuste de canal, sépia e chroma-key ----------

def adjust_channels(matrix: np.ndarray, cyan_red: float, magenta_green: float, yellow_blue: float) -> np.ndarray:
    """Equilíbrio de cores: cada valor vai de -100 a 100 (%).

    Positivo aumenta o primeiro nome da dupla e negativo aumenta o segundo: Ciano/Vermelho soma ao canal R,
    Magenta/Verde ao G e Amarelo/Azul ao B. Mais ciano é menos vermelho, e assim por diante.
    """
    for value in (cyan_red, magenta_green, yellow_blue):
        if not -100 <= value <= 100:
            raise ValueError("Os ajustes de canal devem estar entre -100 e 100.")
    shifts = np.array([cyan_red, magenta_green, yellow_blue]) * 255 / 100
    return clip_to_uint8(as_color(matrix).astype(np.float64) + shifts)


def sepia(matrix: np.ndarray) -> np.ndarray:
    """Tom sépia: cada cor nova é uma mistura fixa de R, G e B que dá uma escala de cinza amarelada."""
    return clip_to_uint8(as_color(matrix).astype(np.float64) @ SEPIA_MATRIX.T)


def chroma_key(matrix: np.ndarray, background: np.ndarray | None, key_color: tuple[float, float, float], distance: float) -> np.ndarray:
    """Troca por `background` os pixels cuja cor está a até `distance` da `key_color` (distância euclidiana em RGB).

    Sem `background` (None), os pixels trocados ficam pretos. O fundo é esticado ao tamanho da imagem.
    """
    if not 0 <= distance <= MAX_KEY_DISTANCE:
        raise ValueError(f"A distância deve estar entre 0 e {MAX_KEY_DISTANCE}.")
    if any(not 0 <= channel <= 255 for channel in key_color):
        raise ValueError("A cor-chave deve ter valores de 0 a 255.")

    image = as_color(matrix)
    height, width = image.shape[:2]
    if background is None:
        replacement = np.zeros_like(image)
    else:
        replacement = as_color(background)
        if replacement.shape[:2] != (height, width):
            replacement = np.stack([resize_image(replacement[:, :, c], height, width, BILINEAR) for c in range(3)], axis=-1)

    difference = image.astype(np.float64) - np.array(key_color, dtype=np.float64)
    close = (difference ** 2).sum(axis=2) <= distance ** 2
    return np.where(close[:, :, None], replacement, image).astype(np.uint8)
