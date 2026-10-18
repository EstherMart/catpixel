import numpy as np
import pytest

from backend.model.geometry import rotate_image, rotated_shape, scale_image

SMALL = np.array([[1, 2], [3, 4]], dtype=np.uint8)
PHOTO = np.random.default_rng(7).integers(0, 256, size=(6, 9), dtype=np.uint8)


def test_scale_with_both_interpolations():
    for method in ("nearest", "bilinear"):
        assert np.array_equal(scale_image(PHOTO, 1, 1, method), PHOTO)  # fator 1 não muda nada
        assert scale_image(PHOTO, 2, 3, method).shape == (18, 18)  # largura x2, altura x3
        assert scale_image(PHOTO, 0.5, 0.5, method).shape == (3, 5)

    blocks = np.array([[1, 1, 2, 2], [1, 1, 2, 2], [3, 3, 4, 4], [3, 3, 4, 4]], dtype=np.uint8)
    assert np.array_equal(scale_image(SMALL, 2, 2, "nearest"), blocks)  # cada pixel vira um bloco 2x2
    assert scale_image(np.array([[0, 100]], dtype=np.uint8), 2, 1, "bilinear").tolist() == [[0, 25, 75, 100]]
    wide = np.array([[0, 100], [100, 200]], dtype=np.uint8)
    assert set(np.unique(scale_image(wide, 3, 3, "nearest"))) <= {0, 100, 200}  # vizinho não cria tons novos
    assert len(set(np.unique(scale_image(wide, 3, 3, "bilinear"))) - {0, 100, 200}) > 0  # bilinear cria tons intermediários

    original = PHOTO.copy()
    scale_image(PHOTO, 2, 2)
    assert np.array_equal(PHOTO, original)
    for invalid in ((0, 1), (-1, 1), (float("nan"), 1), (1000, 1000), (0.01, 0.01)):
        with pytest.raises(ValueError):
            scale_image(PHOTO, *invalid)
    with pytest.raises(ValueError):
        scale_image(PHOTO, 2, 2, "bicubic")


def test_rotation_with_and_without_pivot():
    for method in ("nearest", "bilinear"):
        assert np.array_equal(rotate_image(PHOTO, 0, method), PHOTO)
        assert np.array_equal(rotate_image(PHOTO, 90, method, expand=True), np.rot90(PHOTO))  # anti-horário
        assert np.array_equal(rotate_image(PHOTO, -90, method, expand=True), np.rot90(PHOTO, -1))
        assert np.array_equal(rotate_image(PHOTO, 180, method, expand=True), np.rot90(PHOTO, 2))

    assert rotated_shape((10, 10), 45, expand=True) == (15, 15)  # 10·cos45 + 10·sin45 = 14,14
    assert rotated_shape((6, 9), 90, expand=True) == (9, 6) and rotated_shape((6, 9), 33, expand=False) == (6, 9)

    flat = np.full((21, 21), 150, dtype=np.uint8)
    turned = rotate_image(flat, 45, "bilinear")
    assert turned[10, 10] == 150 and turned[0, 0] == 0  # centro intacto, canto fica preto

    square = np.arange(25, dtype=np.uint8).reshape(5, 5)
    assert np.array_equal(rotate_image(square, 90, "nearest", pivot=(2, 2)), np.rot90(square))  # pivô no centro
    corner = rotate_image(square, 90, "nearest", pivot=(0, 0))
    assert corner.shape == square.shape and corner[0, 0] == square[0, 0]  # o pivô não se move
    assert corner[0].tolist() == square[:, 0].tolist() and not corner[1:].any()  # a 1ª coluna vira a 1ª linha; o resto sai

    for invalid in (lambda: rotate_image(PHOTO, float("nan")), lambda: rotate_image(PHOTO, 10, "x"),
                    lambda: rotate_image(PHOTO, 10, pivot=(1, 1), expand=True), lambda: rotate_image(PHOTO, 10, pivot=(float("inf"), 0))):
        with pytest.raises(ValueError):
            invalid()
