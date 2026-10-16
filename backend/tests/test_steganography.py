import numpy as np
import pytest

from backend.model.steganography import capacity_bytes, hide_message, reveal_message

PHOTO = np.random.default_rng(1).integers(0, 256, size=(40, 40), dtype=np.uint8)


def test_hide_then_reveal_gives_back_the_text():
    assert reveal_message(hide_message(PHOTO, "Olá, gatinho!")) == "Olá, gatinho!"


def test_only_the_lowest_bit_changes():
    result = hide_message(PHOTO, "segredo")
    difference = result.astype(int) - PHOTO.astype(int)
    assert np.abs(difference).max() <= 1


def test_does_not_change_the_input():
    original = PHOTO.copy()
    hide_message(PHOTO, "x")
    assert np.array_equal(PHOTO, original)


def test_image_without_message_reveals_nothing():
    assert reveal_message(PHOTO) is None
    assert reveal_message(np.zeros((40, 40), dtype=np.uint8)) is None


def test_tiny_image_reveals_nothing():
    assert reveal_message(np.zeros((2, 2), dtype=np.uint8)) is None


def test_message_that_fills_the_image_exactly_fits():
    matrix = np.zeros((20, 20), dtype=np.uint8)
    text = "a" * capacity_bytes(matrix)
    assert reveal_message(hide_message(matrix, text)) == text


def test_message_too_long_is_rejected():
    matrix = np.zeros((20, 20), dtype=np.uint8)
    with pytest.raises(ValueError):
        hide_message(matrix, "a" * (capacity_bytes(matrix) + 1))


def test_empty_message_is_rejected():
    with pytest.raises(ValueError):
        hide_message(PHOTO, "")


def test_hiding_twice_keeps_only_the_last_message():
    first = hide_message(PHOTO, "primeira mensagem, mais longa")
    assert reveal_message(hide_message(first, "segunda")) == "segunda"


def test_rejects_color_image():
    with pytest.raises(ValueError):
        hide_message(np.zeros((9, 9, 3), dtype=np.uint8), "x")
