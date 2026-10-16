"""Catálogo das operações que a interface pode pedir. Para criar uma nova, basta registrá-la aqui."""
from dataclasses import dataclass
from typing import Any, Callable

import math

import numpy as np

from backend.model.brightness import adjust_brightness
from backend.model.gamma_log import gamma_correction, log_transformation
from backend.model.negative import negative_image
from backend.model.piecewise_linear import piecewise_linear
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
