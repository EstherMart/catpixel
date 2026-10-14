"""Entrada e saída de imagens. O Pillow é usado somente aqui."""
import io
from typing import BinaryIO

import numpy as np
from PIL import Image


def load_image(source: str | BinaryIO) -> np.ndarray:
    """Lê uma imagem (caminho ou arquivo aberto) e devolve uma matriz uint8 (H, W) em escala de cinza."""
    with Image.open(source) as img:
        return np.array(img.convert("L"), dtype=np.uint8)


def encode_image(matrix: np.ndarray, image_format: str) -> bytes:
    """Codifica a matriz como PNG, BMP ou JPEG e devolve os bytes do arquivo."""
    matrix = np.clip(matrix, 0, 255).astype(np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(matrix).save(buffer, format=image_format)
    return buffer.getvalue()


def save_image(matrix: np.ndarray, path: str) -> None:
    """Grava a matriz como imagem; o formato vem da extensão do arquivo."""
    matrix = np.clip(matrix, 0, 255).astype(np.uint8)
    Image.fromarray(matrix).save(path)
