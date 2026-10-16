"""Esteganografia: esconde texto nos bits menos significativos (LSB) dos pixels.

Formato escondido, lido pixel a pixel (linha por linha), um bit por pixel, do bit mais alto ao mais baixo:
    2 bytes "CP" (assinatura) + 4 bytes com o tamanho da mensagem + mensagem em UTF-8.
"""
import numpy as np

SIGNATURE = b"CP"
LENGTH_BYTES = 4
HEADER_BITS = (len(SIGNATURE) + LENGTH_BYTES) * 8


def capacity_bytes(matrix: np.ndarray) -> int:
    """Quantos bytes de mensagem cabem na imagem."""
    height, width = matrix.shape
    return max(0, (height * width - HEADER_BITS) // 8)


def hide_message(matrix: np.ndarray, text: str) -> np.ndarray:
    """Devolve uma cópia da imagem com `text` escondido. A imagem original não muda."""
    if matrix.ndim != 2:
        raise ValueError("A imagem deve estar em escala de cinza.")
    if not text:
        raise ValueError("Escreva uma mensagem para esconder.")

    message = text.encode("utf-8")
    if len(message) > capacity_bytes(matrix):
        raise ValueError(f"A mensagem não cabe: esta imagem comporta até {capacity_bytes(matrix)} bytes.")

    payload = SIGNATURE + len(message).to_bytes(LENGTH_BYTES, "big") + message
    width = matrix.shape[1]
    result = matrix.copy()

    position = 0
    for byte in payload:
        for shift in range(7, -1, -1):
            y, x = divmod(position, width)
            result[y, x] = (int(result[y, x]) & 0b11111110) | ((byte >> shift) & 1)
            position += 1

    return result


def reveal_message(matrix: np.ndarray) -> str | None:
    """Lê a mensagem escondida. Devolve None se a imagem não tiver uma (ou se ela estiver corrompida)."""
    if matrix.ndim != 2:
        raise ValueError("A imagem deve estar em escala de cinza.")

    height, width = matrix.shape
    total_pixels = height * width
    position = 0

    def read_bytes(count):
        nonlocal position
        data = bytearray()
        for _ in range(count):
            byte = 0
            for _ in range(8):
                y, x = divmod(position, width)
                byte = (byte << 1) | (int(matrix[y, x]) & 1)
                position += 1
            data.append(byte)
        return bytes(data)

    if total_pixels < HEADER_BITS:
        return None
    if read_bytes(len(SIGNATURE)) != SIGNATURE:
        return None

    length = int.from_bytes(read_bytes(LENGTH_BYTES), "big")
    if length == 0 or length > capacity_bytes(matrix):
        return None

    try:
        return read_bytes(length).decode("utf-8")
    except UnicodeDecodeError:
        return None
