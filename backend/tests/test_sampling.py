import numpy as np

from backend.model.sampling import downscale_for_preview


def test_small_image_is_kept():
    matrix = np.zeros((10, 20), dtype=np.uint8)
    assert downscale_for_preview(matrix, 640).shape == (10, 20)


def test_large_image_fits_in_the_limit():
    matrix = np.zeros((1000, 2000), dtype=np.uint8)
    height, width = downscale_for_preview(matrix, 640).shape
    assert max(height, width) <= 640
