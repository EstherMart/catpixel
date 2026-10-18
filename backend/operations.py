"""Catálogo das operações que a interface pode pedir. Para criar uma nova, basta registrá-la aqui."""
from dataclasses import dataclass
from typing import Any, Callable

import math

import numpy as np

from backend.model.brightness import adjust_brightness
from backend.model.convolution import convolve
from backend.model.gamma_log import gamma_correction, log_transformation
from backend.model.histogram import equalize_histogram
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
