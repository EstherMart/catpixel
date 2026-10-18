"""Entrada e saída de imagens. O Pillow é usado somente aqui."""
import io
from typing import BinaryIO

import numpy as np
from PIL import Image


GRAY_MODES = ("1", "L", "LA", "I", "I;16", "F")  # modos do Pillow que são imagens em tons de cinza


def load_image(source: str | BinaryIO) -> np.ndarray:
    """Lê uma imagem (caminho ou arquivo aberto) e devolve uma matriz uint8.

    Imagem em tons de cinza vira (altura, largura). Imagem colorida vira (altura, largura, 3), na ordem R, G, B.
    """
    with Image.open(source) as img:
        mode = "L" if img.mode in GRAY_MODES else "RGB"
        return np.array(img.convert(mode), dtype=np.uint8)


def encode_image(matrix: np.ndarray, image_format: str) -> bytes:
    """Codifica a matriz (cinza ou RGB) como PNG, BMP ou JPEG e devolve os bytes do arquivo."""
    matrix = np.clip(matrix, 0, 255).astype(np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(matrix).save(buffer, format=image_format)
    return buffer.getvalue()


def save_image(matrix: np.ndarray, path: str) -> None:
    """Grava a matriz (cinza ou RGB) como imagem; o formato vem da extensão do arquivo."""
    matrix = np.clip(matrix, 0, 255).astype(np.uint8)
    Image.fromarray(matrix).save(path)
