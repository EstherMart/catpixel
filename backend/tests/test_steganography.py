import numpy as np
import pytest

from backend.model.steganography import capacity_bytes, hide_message, reveal_message

PHOTO = np.random.default_rng(1).integers(0, 256, size=(40, 40), dtype=np.uint8)


def test_hide_and_reveal():
    original = PHOTO.copy()
    result = hide_message(PHOTO, "Olá, gatinho!")
    assert reveal_message(result) == "Olá, gatinho!"
    assert np.abs(result.astype(int) - PHOTO.astype(int)).max() <= 1  # só o bit menos significativo muda
    assert np.array_equal(PHOTO, original)  # a entrada não muda

    assert reveal_message(PHOTO) is None and reveal_message(np.zeros((2, 2), dtype=np.uint8)) is None
    assert reveal_message(hide_message(result, "segunda")) == "segunda"  # só a última mensagem vale

    matrix = np.zeros((20, 20), dtype=np.uint8)
    full = "a" * capacity_bytes(matrix)
    assert reveal_message(hide_message(matrix, full)) == full  # cabe exatamente


def test_hide_rejects_invalid_input():
    matrix = np.zeros((20, 20), dtype=np.uint8)
    for invalid in (lambda: hide_message(matrix, "a" * (capacity_bytes(matrix) + 1)), lambda: hide_message(PHOTO, ""),
                    lambda: hide_message(np.zeros((9, 9, 3), dtype=np.uint8), "x")):
        with pytest.raises(ValueError):
            invalid()
