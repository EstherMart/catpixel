import numpy as np
import pytest

from backend.model.convolution import convolve

IDENTITY_3 = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
PHOTO = np.random.default_rng(4).integers(0, 256, size=(12, 15), dtype=np.uint8)


def box(size):
    return [[1] * size for _ in range(size)]


@pytest.mark.parametrize("size", [3, 5, 7, 9, 11])
def test_output_has_the_same_size_for_every_kernel_size(size):
    assert convolve(PHOTO, box(size), size * size).shape == PHOTO.shape


def test_identity_kernel_keeps_the_image():
    assert np.array_equal(convolve(PHOTO, IDENTITY_3), PHOTO)


def test_box_filter_keeps_a_flat_image():
    flat = np.full((6, 6), 90, dtype=np.uint8)
    assert np.array_equal(convolve(flat, box(5), 25), flat)


def test_small_matrix_gives_the_expected_result():
    matrix = np.array([[0, 0, 0],
                       [0, 90, 0],
                       [0, 0, 0]], dtype=np.uint8)
    # média 3x3: o impulso de 90 espalha 90/9 = 10 para o centro e para os 8 vizinhos
    assert np.array_equal(convolve(matrix, box(3), 9), np.full((3, 3), 10, dtype=np.uint8))


def test_border_pixels_repeat_the_nearest_pixel():
    matrix = np.array([[0, 0, 100]], dtype=np.uint8)
    take_right_neighbor = [[0, 0, 0], [1, 0, 0], [0, 0, 0]]  # na convolução, o peso à esquerda lê o pixel à direita
    # o último pixel não tem vizinho à direita: a borda repete o 100
    assert convolve(matrix, take_right_neighbor).tolist() == [[0, 100, 100]]


def test_impulse_reproduces_the_kernel_as_given():
    matrix = np.array([[0, 0, 0], [0, 100, 0], [0, 0, 0]], dtype=np.uint8)
    kernel = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    result = convolve(matrix, kernel, 10)
    # convolução de um impulso devolve o filtro (a correlação o devolveria girado)
    assert result.tolist() == [[10, 20, 30], [40, 50, 60], [70, 80, 90]]


def test_values_are_clipped_by_default_and_normalized_on_request():
    edges = [[0, -1, 0], [-1, 4, -1], [0, -1, 0]]
    clipped = convolve(PHOTO, edges)
    normalized = convolve(PHOTO, edges, normalize=True)
    assert int(normalized.min()) == 0 and int(normalized.max()) == 255
    assert not np.array_equal(clipped, normalized)


def test_does_not_change_the_input():
    original = PHOTO.copy()
    convolve(PHOTO, box(3), 9)
    assert np.array_equal(PHOTO, original)


@pytest.mark.parametrize("kernel", [
    [[1, 1], [1, 1]],                 # dimensão par
    [[1, 1, 1], [1, 1, 1]],           # não quadrado
    [[1] * 17 for _ in range(17)],    # grande demais
    [[1, 1, "a"], [1, 1, 1], [1, 1, 1]],
    [],
])
def test_rejects_invalid_kernels(kernel):
    with pytest.raises(ValueError):
        convolve(PHOTO, kernel)


@pytest.mark.parametrize("divisor", [0, float("nan"), float("inf")])
def test_rejects_invalid_divisor(divisor):
    with pytest.raises(ValueError):
        convolve(PHOTO, IDENTITY_3, divisor)
