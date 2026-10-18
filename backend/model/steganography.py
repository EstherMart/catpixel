"""Esteganografia: esconde texto nos bits menos significativos (LSB) dos pixels.

Formato escondido, lido valor a valor na ordem da imagem (linha por linha e, nas coloridas, R, G, B de
cada pixel), um bit por valor, do bit mais alto ao mais baixo:
    2 bytes "CP" (assinatura) + 4 bytes com o tamanho da mensagem + mensagem em UTF-8.
Numa imagem em cinza isso é um bit por pixel; numa colorida são três bits por pixel.
"""
import numpy as np

SIGNATURE = b"CP"
LENGTH_BYTES = 4
HEADER_BITS = (len(SIGNATURE) + LENGTH_BYTES) * 8


def _check_matrix(matrix: np.ndarray) -> None:
    if matrix.ndim not in (2, 3):
        raise ValueError("A imagem deve ser em tons de cinza ou colorida.")


def capacity_bytes(matrix: np.ndarray) -> int:
    """Quantos bytes de mensagem cabem na imagem."""
    return max(0, (matrix.size - HEADER_BITS) // 8)


def hide_message(matrix: np.ndarray, text: str) -> np.ndarray:
    """Devolve uma cópia da imagem com `text` escondido. A imagem original não muda."""
    _check_matrix(matrix)
    if not text:
        raise ValueError("Escreva uma mensagem para esconder.")

    message = text.encode("utf-8")
    if len(message) > capacity_bytes(matrix):
        raise ValueError(f"A mensagem não cabe: esta imagem comporta até {capacity_bytes(matrix)} bytes.")

    payload = SIGNATURE + len(message).to_bytes(LENGTH_BYTES, "big") + message
    result = matrix.copy()
    values = result.reshape(-1)  # visão linear da mesma memória: mexer nela altera `result`

    position = 0
    for byte in payload:
        for shift in range(7, -1, -1):
            values[position] = (int(values[position]) & 0b11111110) | ((byte >> shift) & 1)
            position += 1

    return result


def reveal_message(matrix: np.ndarray) -> str | None:
    """Lê a mensagem escondida. Devolve None se a imagem não tiver uma (ou se ela estiver corrompida)."""
    _check_matrix(matrix)
    values = matrix.reshape(-1)
    position = 0

    def read_bytes(count):
        nonlocal position
        data = bytearray()
        for _ in range(count):
            byte = 0
            for _ in range(8):
                byte = (byte << 1) | (int(values[position]) & 1)
                position += 1
            data.append(byte)
        return bytes(data)

    if values.size < HEADER_BITS:
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
