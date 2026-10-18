import numpy as np

from backend.model.sampling import downscale_for_preview


def test_preview_keeps_small_images_and_shrinks_large_ones_to_the_limit():
    assert downscale_for_preview(np.zeros((10, 20), dtype=np.uint8), 640).shape == (10, 20)
    height, width = downscale_for_preview(np.zeros((1000, 2000), dtype=np.uint8), 640).shape
    assert max(height, width) <= 640
