import numpy as np

from backend.model.histogram import build_equalization_lut, compute_histogram, equalize_histogram


def test_histogram_counts_each_intensity():
    matrix = np.array([[0, 0, 5], [5, 5, 255]], dtype=np.uint8)
    counts = compute_histogram(matrix)
    assert len(counts) == 256 and sum(counts) == matrix.size
    assert (counts[0], counts[5], counts[255]) == (2, 3, 1)


def test_equalization_spreads_tones_keeps_their_order_and_leaves_flat_images_alone():
    assert set(np.unique(equalize_histogram(np.array([[100] * 4, [101] * 4], dtype=np.uint8)))) == {0, 255}

    low_contrast = np.random.default_rng(3).integers(100, 140, size=(40, 40), dtype=np.uint8)
    result = equalize_histogram(low_contrast)
    assert int(result.min()) == 0 and int(result.max()) == 255

    lut = build_equalization_lut(compute_histogram(low_contrast))
    assert lut == sorted(lut)

    flat = np.full((4, 4), 77, dtype=np.uint8)
    assert np.array_equal(equalize_histogram(flat), flat)
    assert low_contrast.min() >= 100  # a entrada não muda
