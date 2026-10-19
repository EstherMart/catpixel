import numpy as np
import pytest

from backend.model.spatial_filters import (
    gaussian_filter,
    gaussian_kernel,
    gradient_magnitude,
    high_boost_filter,
    laplacian_filter,
    mean_filter,
    median_filter,
    sobel_components,
    sobel_x_filter,
    sobel_y_filter,
)

PHOTO = np.random.default_rng(5).integers(0, 256, size=(20, 24), dtype=np.uint8)
FLAT = np.full((8, 8), 120, dtype=np.uint8)
STEP = np.hstack([np.zeros((8, 4), dtype=np.uint8), np.full((8, 4), 200, dtype=np.uint8)])  # borda vertical
SALT = np.full((7, 7), 100, dtype=np.uint8)
SALT[3, 3] = 255


def test_smoothing_filters():
    for filter_ in (mean_filter, gaussian_filter, median_filter):
        for size in (3, 9):
            assert filter_(PHOTO, size).shape == PHOTO.shape
            assert np.array_equal(filter_(FLAT, size), FLAT)

    impulse = np.zeros((3, 3), dtype=np.uint8)
    impulse[1, 1] = 90
    assert np.array_equal(mean_filter(impulse, 3), np.full((3, 3), 10, dtype=np.uint8))

    kernel, divisor = gaussian_kernel(3)
    assert kernel == [[1, 2, 1], [2, 4, 2], [1, 2, 1]] and divisor == 16
    spot = np.zeros((9, 9), dtype=np.uint8)
    spot[4, 4] = 255
    assert int(gaussian_filter(spot, 5)[4, 4]) > int(mean_filter(spot, 5)[4, 4])  # borra menos que a média

    assert np.array_equal(median_filter(SALT, 3), np.full((7, 7), 100, dtype=np.uint8))  # remove o ponto isolado
    assert int(mean_filter(SALT, 3)[3, 3]) > 100  # a média não remove
    assert median_filter(np.arange(1, 10, dtype=np.uint8).reshape(3, 3), 3)[1, 1] == 5


def test_laplacian_and_high_boost():
    assert np.array_equal(laplacian_filter(FLAT), FLAT)
    sharpened = laplacian_filter(STEP)
    assert int(sharpened[4, 3]) == 0 and int(sharpened[4, 4]) == 255  # realce nos dois lados da borda
    for diagonals in (False, True):
        shown = laplacian_filter(PHOTO, diagonals=diagonals, sharpen=False)
        assert int(shown.min()) == 0 and int(shown.max()) == 255  # normalizado só para exibição

    assert np.array_equal(high_boost_filter(PHOTO, 3, 0), PHOTO)
    soft = np.hstack([np.full((8, 4), 100, dtype=np.uint8), np.full((8, 4), 140, dtype=np.uint8)])
    unsharp, boosted = high_boost_filter(soft, 3, 1), high_boost_filter(soft, 3, 3)
    assert int(unsharp[4, 4]) > 140 and int(boosted[4, 4]) >= int(unsharp[4, 4])
    assert int(unsharp[4, 3]) < 100 and int(boosted[4, 3]) <= int(unsharp[4, 3])


def test_invalid_sizes_and_negative_k_are_rejected():
    for size in (0, 2, 4, 17):
        with pytest.raises(ValueError):
            mean_filter(PHOTO, size)
    with pytest.raises(ValueError):
        high_boost_filter(PHOTO, 3, -1)

def test_sobel_and_gradient():
    # Uma região uniforme não possui bordas.
    gx, gy = sobel_components(FLAT)

    assert np.allclose(gx, 0)
    assert np.allclose(gy, 0)

    # STEP possui uma borda vertical.
    # Portanto, a variação na direção X deve ser forte.
    gx, gy = sobel_components(STEP)

    assert np.max(np.abs(gx)) > 0
    assert np.max(np.abs(gy)) == 0

    sobel_x = sobel_x_filter(STEP)
    sobel_y = sobel_y_filter(STEP)
    magnitude = gradient_magnitude(STEP)

    # O processamento deve preservar o tamanho da imagem.
    assert sobel_x.shape == STEP.shape
    assert sobel_y.shape == STEP.shape
    assert magnitude.shape == STEP.shape

    # As imagens prontas para exibição devem ser uint8.
    assert sobel_x.dtype == np.uint8
    assert sobel_y.dtype == np.uint8
    assert magnitude.dtype == np.uint8

    # Longe da borda, a magnitude deve ser zero.
    assert magnitude[4, 0] == 0

    # Na região da borda deve existir resposta.
    assert magnitude[4, 3] > 0 or magnitude[4, 4] > 0
