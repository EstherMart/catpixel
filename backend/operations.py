"""Catálogo das operações que a interface pode pedir. Para criar uma nova, basta registrá-la aqui."""
from dataclasses import dataclass
from typing import Any, Callable

import base64
import io
import math

import numpy as np
from PIL import UnidentifiedImageError

from backend.model.brightness import adjust_brightness
from backend.model.convolution import convolve
from backend.model.gamma_log import gamma_correction, log_transformation
from backend.model.geometry import BILINEAR, NEAREST, rotate_image, rotated_shape, scale_image, scaled_shape
from backend.model.frequency import DFT, FFT, filter_with_mask
from backend.model.histogram import equalize_histogram
from backend.model.image_io import load_image
from backend.model.negative import negative_image
from backend.model.piecewise_linear import piecewise_linear
from backend.model.spatial_filters import (
    gaussian_filter,
    high_boost_filter,
    laplacian_filter,
    mean_filter,
    median_filter,
)
from backend.model.steganography import hide_message
from backend.model.thresholding import threshold_image

Params = dict[str, Any]


@dataclass(frozen=True)
class Operation:
    label: Callable[[Params], str]
    run: Callable[[np.ndarray, Params], np.ndarray]
    # (altura, largura) do resultado, para operações que mudam o tamanho da imagem; None = mesmo tamanho
    result_shape: Callable[[tuple[int, int], Params], tuple[int, int]] | None = None


def _int_param(params: Params, name: str) -> int:
    value = params.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"O parâmetro '{name}' deve ser um número inteiro.")
    return value


def _number_param(params: Params, name: str) -> float:
    value = params.get(name)

    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(
            f"O parâmetro '{name}' deve ser um número finito."
        )

    return float(value)


def _text_param(params: Params, name: str) -> str:
    value = params.get(name)
    if not isinstance(value, str):
        raise ValueError(f"O parâmetro '{name}' deve ser um texto.")
    return value


def _method_param(params: Params) -> str:
    """O navegador manda 0 (vizinho mais próximo) ou 1 (bilinear)."""
    return BILINEAR if _number_param(params, "method") else NEAREST


METHOD_NAMES = {NEAREST: "vizinho mais próximo", BILINEAR: "bilinear"}


def _pivot(matrix: np.ndarray, params: Params) -> tuple[float, float]:
    """O pivô chega em porcentagem da imagem (0 a 100 em cada eixo) e é convertido em pixels."""
    height, width = matrix.shape
    percent_x, percent_y = _number_param(params, "pivot_x"), _number_param(params, "pivot_y")
    if not (0 <= percent_x <= 100 and 0 <= percent_y <= 100):
        raise ValueError("O pivô deve estar entre 0% e 100% em cada eixo.")
    return percent_x / 100 * (width - 1), percent_y / 100 * (height - 1)


def _mask_param(params: Params, name: str) -> np.ndarray:
    """A máscara do espectro chega como imagem PNG em base64 (sem o prefixo "data:")."""
    text = _text_param(params, name)
    try:
        return load_image(io.BytesIO(base64.b64decode(text, validate=True)))
    except (ValueError, UnidentifiedImageError, OSError):
        raise ValueError(f"O parâmetro '{name}' deve ser uma imagem PNG codificada em base64.")


def _kernel_param(params: Params, name: str) -> list[list[float]]:
    value = params.get(name)
    if not isinstance(value, list) or not all(isinstance(row, list) for row in value):
        raise ValueError(f"O parâmetro '{name}' deve ser uma matriz (lista de listas) de números.")
    return value


OPERATIONS: dict[str, Operation] = {
    "threshold": Operation(
        label=lambda params: f"Limiarização ({params['limit']})",
        run=lambda matrix, params: threshold_image(matrix, _int_param(params, "limit")),
    ),

    "negative": Operation(
        label=lambda params: "Negativo",
        run=lambda matrix, params: negative_image(matrix),
    ),

    "brightness": Operation(
        label=lambda params: f"Brilho (x{params['factor']})",
        run=lambda matrix, params: adjust_brightness(
            matrix, _number_param(params, "factor")
        ),
    ),

    "gamma": Operation(
        label=lambda params: f"Gama ({params['gamma']})",
        run=lambda matrix, params: gamma_correction(
            matrix, _number_param(params, "gamma")
        ),
    ),

    "log": Operation(
        label=lambda params: "Logaritmo",
        run=lambda matrix, params: log_transformation(matrix),
    ),

    "piecewise": Operation(
        label=lambda params: (
            f"Linear por partes ({params['r1']},{params['s1']}) ({params['r2']},{params['s2']})"
        ),
        run=lambda matrix, params: piecewise_linear(
            matrix,
            _number_param(params, "r1"),
            _number_param(params, "s1"),
            _number_param(params, "r2"),
            _number_param(params, "s2"),
        ),
    ),

    "equalize": Operation(
        label=lambda params: "Equalização de histograma",
        run=lambda matrix, params: equalize_histogram(matrix),
    ),

    "convolution": Operation(
        label=lambda params: f"Convolução {len(params['kernel'])}x{len(params['kernel'])}",
        run=lambda matrix, params: convolve(
            matrix,
            _kernel_param(params, "kernel"),
            _number_param(params, "divisor"),
            bool(_number_param(params, "normalize")),
        ),
    ),

    "mean": Operation(
        label=lambda params: f"Média {params['size']}x{params['size']}",
        run=lambda matrix, params: mean_filter(matrix, _int_param(params, "size")),
    ),

    "gaussian": Operation(
        label=lambda params: f"Gaussiana {params['size']}x{params['size']}",
        run=lambda matrix, params: gaussian_filter(matrix, _int_param(params, "size")),
    ),

    "median": Operation(
        label=lambda params: f"Mediana {params['size']}x{params['size']}",
        run=lambda matrix, params: median_filter(matrix, _int_param(params, "size")),
    ),

    "laplacian": Operation(
        label=lambda params: "Laplaciano (aguçamento)" if params["sharpen"] else "Laplaciano (só a imagem laplaciana)",
        run=lambda matrix, params: laplacian_filter(
            matrix,
            diagonals=bool(_number_param(params, "diagonals")),
            sharpen=bool(_number_param(params, "sharpen")),
        ),
    ),

    "highboost": Operation(
        label=lambda params: f"High-boost (k={params['k']})",
        run=lambda matrix, params: high_boost_filter(
            matrix,
            _int_param(params, "size"),
            _number_param(params, "k"),
            gaussian=bool(_number_param(params, "gaussian")),
        ),
    ),

    "scale": Operation(
        label=lambda params: f"Escala (x{params['scale_x']}, y{params['scale_y']}, {METHOD_NAMES[_method_param(params)]})",
        run=lambda matrix, params: scale_image(
            matrix, _number_param(params, "scale_x"), _number_param(params, "scale_y"), _method_param(params)
        ),
        result_shape=lambda shape, params: scaled_shape(
            shape, _number_param(params, "scale_x"), _number_param(params, "scale_y")
        ),
    ),

    "rotate": Operation(
        label=lambda params: f"Rotação ({params['angle']}°, {METHOD_NAMES[_method_param(params)]})",
        run=lambda matrix, params: rotate_image(
            matrix,
            _number_param(params, "angle"),
            _method_param(params),
            expand=bool(_number_param(params, "expand")),
        ),
        result_shape=lambda shape, params: rotated_shape(
            shape, _number_param(params, "angle"), bool(_number_param(params, "expand"))
        ),
    ),

    "rotate_pivot": Operation(
        label=lambda params: (
            f"Rotação com pivô ({params['angle']}°, pivô {params['pivot_x']}%, {params['pivot_y']}%, "
            f"{METHOD_NAMES[_method_param(params)]})"
        ),
        run=lambda matrix, params: rotate_image(
            matrix,
            _number_param(params, "angle"),
            _method_param(params),
            pivot=_pivot(matrix, params),
        ),
    ),

    "frequency_filter": Operation(
        label=lambda params: f"Filtro no espectro ({'DFT' if params['algorithm'] else 'FFT'})",
        run=lambda matrix, params: filter_with_mask(
            matrix,
            _mask_param(params, "mask"),
            DFT if _number_param(params, "algorithm") else FFT,
            bool(_number_param(params, "normalize")),
        ),
    ),

    "hide_message": Operation(
        label=lambda params: "Esteganografia (mensagem escondida)",  # o texto secreto não vai para o histórico
        run=lambda matrix, params: hide_message(matrix, _text_param(params, "text")),
    ),
}


def run_operation(name: str, matrix: np.ndarray, params: Params) -> tuple[str, np.ndarray]:
    """Executa a operação e devolve (rótulo para o histórico, nova matriz)."""
    if name not in OPERATIONS:
        raise KeyError(name)
    operation = OPERATIONS[name]
    result = operation.run(matrix, params)  # valida os parâmetros antes de montar o rótulo
    return operation.label(params), result


def result_shape(name: str, shape: tuple[int, int], params: Params) -> tuple[int, int]:
    """(altura, largura) que o resultado da operação terá, sem calcular a imagem."""
    operation = OPERATIONS[name]
    return operation.result_shape(shape, params) if operation.result_shape else shape
