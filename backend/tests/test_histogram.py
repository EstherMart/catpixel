import numpy as np

from backend.model.histogram import build_equalization_lut, compute_histogram, equalize_histogram


def test_histogram_counts_each_intensity():
    matrix = np.array([[0, 0, 5], [5, 5, 255]], dtype=np.uint8)
    counts = compute_histogram(matrix)
    assert len(counts) == 256
    assert (counts[0], counts[5], counts[255]) == (2, 3, 1)
    assert sum(counts) == matrix.size


def test_equalization_of_a_known_histogram():
    # 4 pixels em 100, 4 em 101: cdf = 4, 8 → os tons vão para 0 e 255
    matrix = np.array([[100] * 4, [101] * 4], dtype=np.uint8)
    assert set(np.unique(equalize_histogram(matrix))) == {0, 255}


def test_equalization_spreads_a_low_contrast_image():
    rng = np.random.default_rng(3)
    matrix = rng.integers(100, 140, size=(40, 40), dtype=np.uint8)
    result = equalize_histogram(matrix)
    assert int(result.min()) == 0 and int(result.max()) == 255


def test_equalization_keeps_the_order_of_tones():
    lut = build_equalization_lut(compute_histogram(np.arange(256, dtype=np.uint8).reshape(16, 16) // 3))
    assert lut == sorted(lut)


def test_flat_image_is_kept_as_is():
    matrix = np.full((4, 4), 77, dtype=np.uint8)
    assert np.array_equal(equalize_histogram(matrix), matrix)


def test_equalization_does_not_change_the_input():
    matrix = np.array([[10, 20], [30, 40]], dtype=np.uint8)
    equalize_histogram(matrix)
    assert matrix.tolist() == [[10, 20], [30, 40]]
