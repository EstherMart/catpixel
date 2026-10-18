import numpy as np
import pytest

from backend.model.convolution import convolve

PHOTO = np.random.default_rng(4).integers(0, 256, size=(12, 15), dtype=np.uint8)
IDENTITY_3 = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]


def box(size):
    return [[1] * size for _ in range(size)]


def test_convolution():
    for size in (3, 5, 9, 11):
        assert convolve(PHOTO, box(size), size * size).shape == PHOTO.shape  # mesmo tamanho da original
    assert np.array_equal(convolve(PHOTO, IDENTITY_3), PHOTO)
    flat = np.full((6, 6), 90, dtype=np.uint8)
    assert np.array_equal(convolve(flat, box(5), 25), flat)

    impulse = np.zeros((3, 3), dtype=np.uint8)
    impulse[1, 1] = 90
    assert np.array_equal(convolve(impulse, box(3), 9), np.full((3, 3), 10, dtype=np.uint8))

    centered = np.zeros((3, 3), dtype=np.uint8)
    centered[1, 1] = 100
    kernel = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    assert convolve(centered, kernel, 10).tolist() == [[10, 20, 30], [40, 50, 60], [70, 80, 90]]  # impulso devolve o filtro

    right_neighbor = [[0, 0, 0], [1, 0, 0], [0, 0, 0]]
    assert convolve(np.array([[0, 0, 100]], dtype=np.uint8), right_neighbor).tolist() == [[0, 100, 100]]  # borda repete o pixel

    edges = [[0, -1, 0], [-1, 4, -1], [0, -1, 0]]
    normalized = convolve(PHOTO, edges, normalize=True)
    assert int(normalized.min()) == 0 and int(normalized.max()) == 255
    assert not np.array_equal(convolve(PHOTO, edges), normalized)

    for kernel in ([[1, 1], [1, 1]], [[1, 1, 1], [1, 1, 1]], [[1] * 17 for _ in range(17)],
                   [[1, 1, "a"], [1, 1, 1], [1, 1, 1]], []):
        with pytest.raises(ValueError):
            convolve(PHOTO, kernel)
    for divisor in (0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            convolve(PHOTO, IDENTITY_3, divisor)
