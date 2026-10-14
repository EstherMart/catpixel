import numpy as np

MAX_INTENSITY = 255


def threshold_image(matrix: np.ndarray, threshold: int) -> np.ndarray:
    """Limiarização global: intensidade >= limiar vira 255, o resto vira 0."""
    if matrix.ndim != 2:
        raise ValueError("A imagem deve estar em escala de cinza.")
    if not 0 <= threshold <= MAX_INTENSITY:
        raise ValueError("O limiar deve estar entre 0 e 255.")

    height, width = matrix.shape
    binary_image = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            if matrix[y, x] >= threshold:
                binary_image[y, x] = MAX_INTENSITY

    return binary_image
