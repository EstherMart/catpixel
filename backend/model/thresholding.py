import numpy as np

def threshold_image(matrix: np.ndarray, threshold: int) -> np.ndarray:
    """ 
    Realiza limiarização global.
        r < threshold  -> 0
        r >= threshold -> 255
    """

    if matrix.ndim != 2:
        raise ValueError("A imagem deve estar em escala de cinza.")

    if not 0 <= threshold <= 255:
        raise ValueError("O limiar deve estar entre 0 e 255.")

    height, width = matrix.shape
    binary_image = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            intensity = matrix[y, x]
            if intensity >= threshold:
                binary_image[y, x] = 255 
                #pixel branco, não colocou o caso intensity < threshold binary_image = 0, pois ela já está zero
                #afinal binary_image já é uma matriz de zeros, então quis evitar redundância
    return binary_image