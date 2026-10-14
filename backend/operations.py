"""Catálogo das operações que a interface pode pedir. Para criar uma nova, basta registrá-la aqui."""
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

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


OPERATIONS: dict[str, Operation] = {
    "threshold": Operation(
        label=lambda params: f"Limiarização ({params['limit']})",
        run=lambda matrix, params: threshold_image(matrix, _int_param(params, "limit")),
    ),
}


def run_operation(name: str, matrix: np.ndarray, params: Params) -> tuple[str, np.ndarray]:
    """Executa a operação e devolve (rótulo para o histórico, nova matriz)."""
    if name not in OPERATIONS:
        raise KeyError(name)
    operation = OPERATIONS[name]
    result = operation.run(matrix, params)  # valida os parâmetros antes de montar o rótulo
    return operation.label(params), result
