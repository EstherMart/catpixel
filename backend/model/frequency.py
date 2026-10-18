"""Domínio da frequência: DFT e FFT próprias, espectro deslocado e filtragem por máscara.

Nada daqui usa `numpy.fft`. As duas transformadas são escritas à mão:
- `dft2`: a definição, com a matriz de Fourier (O(N²) por linha; lenta, por isso só para imagens pequenas);
- `fft2`: Cooley-Tukey radix-2 (O(N log N)), que exige lados potência de 2 e por isso preenche com zeros.
"""
import math
import time

import numpy as np

from backend.model.convolution import clip_to_uint8, normalize_for_display
from backend.model.geometry import BILINEAR, resize_image

FFT = "fft"
DFT = "dft"
ALGORITHMS = (FFT, DFT)
MAX_DFT_SIDE = 1024  # a DFT ingênua cresce com o cubo do lado (1024 leva cerca de 1 s); acima disso demora demais
MAX_FFT_SIDE = 2048  # lado máximo depois do preenchimento (2048 x 2048 já ocupa 64 MB em complexos)


# ---------- transformada discreta de Fourier (definição) ----------

def _dft_matrix(size: int) -> np.ndarray:
    """Matriz W[k, n] = e^(-j·2π·k·n / N): multiplicá-la por um vetor dá a DFT dele."""
    index = np.arange(size)
    return np.exp(-2j * np.pi * np.outer(index, index) / size)


def dft2(matrix: np.ndarray) -> np.ndarray:
    """DFT 2D pela definição: F = W_altura · f · W_largura (a transformada é separável)."""
    height, width = matrix.shape
    return _dft_matrix(height) @ matrix.astype(np.complex128) @ _dft_matrix(width)


def idft2(spectrum: np.ndarray) -> np.ndarray:
    """Inversa da DFT 2D: usa a matriz conjugada e divide por altura · largura."""
    height, width = spectrum.shape
    return np.conj(_dft_matrix(height)) @ spectrum @ np.conj(_dft_matrix(width)) / (height * width)


# ---------- transformada rápida de Fourier (radix-2) ----------

def _bit_reversal(size: int) -> np.ndarray:
    """Posição de cada elemento depois de inverter a ordem dos bits do índice (0b001 → 0b100 etc.)."""
    bits = size.bit_length() - 1
    order = np.zeros(size, dtype=int)
    for index in range(size):
        reversed_index = 0
        for bit in range(bits):
            reversed_index |= ((index >> bit) & 1) << (bits - 1 - bit)
        order[index] = reversed_index
    return order


def _fft_last_axis(values: np.ndarray, inverse: bool) -> np.ndarray:
    """FFT de todos os vetores do último eixo de uma vez (o tamanho precisa ser potência de 2)."""
    size = values.shape[-1]
    if size & (size - 1):
        raise ValueError("A FFT radix-2 exige tamanhos que sejam potência de 2.")
    values = values[..., _bit_reversal(size)].astype(np.complex128)

    sign = 1 if inverse else -1
    half = 1
    while half < size:
        # junta pares de blocos de tamanho `half`: X = par + w·ímpar e Y = par − w·ímpar, com w = e^(∓jπk/half)
        blocks = values.reshape(*values.shape[:-1], size // (2 * half), 2, half)
        even, odd = blocks[..., 0, :], blocks[..., 1, :]
        twiddle = np.exp(sign * 1j * np.pi * np.arange(half) / half)
        odd = odd * twiddle
        values = np.stack([even + odd, even - odd], axis=-2).reshape(values.shape)
        half *= 2
    return values


def _fft2(matrix: np.ndarray, inverse: bool) -> np.ndarray:
    rows = _fft_last_axis(matrix, inverse)  # transforma as linhas
    return _fft_last_axis(rows.T, inverse).T  # e depois as colunas


def fft2(matrix: np.ndarray) -> np.ndarray:
    """FFT 2D. Os dois lados precisam ser potência de 2 (veja `pad_to_power_of_two`)."""
    return _fft2(matrix, inverse=False)


def ifft2(spectrum: np.ndarray) -> np.ndarray:
    """Inversa da FFT 2D (divide por altura · largura)."""
    return _fft2(spectrum, inverse=True) / spectrum.size


def next_power_of_two(value: int) -> int:
    return 1 << (value - 1).bit_length()


def pad_to_power_of_two(matrix: np.ndarray) -> np.ndarray:
    """Completa com zeros (embaixo e à direita) até os dois lados serem potência de 2."""
    height, width = matrix.shape
    padded = np.zeros((next_power_of_two(height), next_power_of_two(width)), dtype=matrix.dtype)
    padded[:height, :width] = matrix
    return padded


# ---------- espectro deslocado ----------

def shift(spectrum: np.ndarray) -> np.ndarray:
    """Leva a frequência zero (o canto da DFT) para o centro da imagem do espectro."""
    height, width = spectrum.shape
    return np.roll(spectrum, (height // 2, width // 2), axis=(0, 1))


def unshift(spectrum: np.ndarray) -> np.ndarray:
    """Desfaz `shift`."""
    height, width = spectrum.shape
    return np.roll(spectrum, (-(height // 2), -(width // 2)), axis=(0, 1))


def spectrum_shape(shape: tuple[int, int], algorithm: str) -> tuple[int, int]:
    """(altura, largura) do espectro que a imagem gera. A FFT arredonda para potências de 2."""
    _check_algorithm(algorithm)
    height, width = shape
    if algorithm == DFT:
        if max(height, width) > MAX_DFT_SIDE:
            raise ValueError(
                f"A DFT ingênua só aceita imagens de até {MAX_DFT_SIDE} pixels de lado. Use a FFT."
            )
        return height, width
    padded = (next_power_of_two(height), next_power_of_two(width))
    if max(padded) > MAX_FFT_SIDE:
        raise ValueError(
            f"A imagem é grande demais para o domínio da frequência (até {MAX_FFT_SIDE} pixels de lado "
            "depois de completar até potência de 2). Reduza a imagem com a escala."
        )
    return padded


def _check_algorithm(algorithm: str) -> None:
    if algorithm not in ALGORITHMS:
        raise ValueError("O algoritmo deve ser 'fft' ou 'dft'.")


def compute_spectrum(matrix: np.ndarray, algorithm: str = FFT) -> np.ndarray:
    """Espectro (complexo) deslocado da imagem, com a frequência zero no centro."""
    if matrix.ndim != 2:
        raise ValueError("A imagem deve estar em escala de cinza.")
    spectrum_shape(matrix.shape, algorithm)  # valida o tamanho antes de gastar tempo
    if algorithm == DFT:
        return shift(dft2(matrix))
    return shift(fft2(pad_to_power_of_two(matrix)))


def spectrum_image(spectrum: np.ndarray) -> np.ndarray:
    """Imagem do espectro para exibição: s = 255 · ln(1 + |F|) / ln(1 + |F|máx).

    O logaritmo é necessário porque a frequência zero é milhares de vezes maior que as outras,
    e sem ele só um ponto central apareceria.
    """
    magnitude = np.abs(spectrum)
    return clip_to_uint8(255 * np.log1p(magnitude) / math.log1p(magnitude.max() or 1))


def timed_spectrum(matrix: np.ndarray, algorithm: str = FFT) -> tuple[np.ndarray, float]:
    """Calcula o espectro e devolve também quantos segundos levou."""
    start = time.perf_counter()
    spectrum = compute_spectrum(matrix, algorithm)
    return spectrum, time.perf_counter() - start


# ---------- filtragem pelo espectro editado ----------

def filter_with_mask(matrix: np.ndarray, mask: np.ndarray, algorithm: str = FFT, normalize: bool = False) -> np.ndarray:
    """Filtra a imagem multiplicando o espectro pela máscara e aplicando a transformada inversa.

    - `mask` é uma imagem em tons de cinza do tamanho do espectro: 0 (preto) zera a frequência,
      255 (branco) a mantém e os cinzas a atenuam. Se o tamanho for outro, ela é redimensionada.
    - O resultado volta ao tamanho original da imagem (o preenchimento da FFT é descartado).
    - Valores fora de 0 a 255 são cortados, ou, com `normalize=True`, ajustados para caber.
    """
    if mask.ndim != 2:
        raise ValueError("A máscara deve ser uma imagem em escala de cinza.")
    spectrum = compute_spectrum(matrix, algorithm)
    if mask.shape != spectrum.shape:
        mask = resize_image(mask, *spectrum.shape, BILINEAR)

    filtered = unshift(spectrum * (mask.astype(np.float64) / 255))
    restored = idft2(filtered) if algorithm == DFT else ifft2(filtered)
    height, width = matrix.shape
    values = restored.real[:height, :width]
    return normalize_for_display(values) if normalize else clip_to_uint8(values)
