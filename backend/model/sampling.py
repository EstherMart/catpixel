import numpy as np


def downscale_for_preview(matrix: np.ndarray, max_side: int) -> np.ndarray:
    """Reduz a imagem pegando 1 pixel a cada `step`, até o maior lado caber em `max_side`."""
    step = -(-max(matrix.shape[:2]) // max_side)  # divisão com arredondamento para cima
    return matrix[::step, ::step]
