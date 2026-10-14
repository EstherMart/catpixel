import numpy as np
import pytest

from backend.model.thresholding import threshold_image


def test_small_matrix_gives_the_expected_result():
    matrix = np.array([[10, 127, 128],
                       [200, 0, 255]], dtype=np.uint8)
    expected = np.array([[0, 0, 255],
                         [255, 0, 255]], dtype=np.uint8)

    assert np.array_equal(threshold_image(matrix, 128), expected)


def test_output_only_has_black_and_white():
    matrix = np.arange(256, dtype=np.uint8).reshape(16, 16)
    assert set(np.unique(threshold_image(matrix, 100))) == {0, 255}


def test_does_not_change_the_input():
    matrix = np.array([[200]], dtype=np.uint8)
    threshold_image(matrix, 255)
    assert matrix[0, 0] == 200


@pytest.mark.parametrize("limit", [-1, 256])
def test_rejects_limit_out_of_range(limit):
    with pytest.raises(ValueError):
        threshold_image(np.zeros((2, 2), dtype=np.uint8), limit)


def test_rejects_color_image():
    with pytest.raises(ValueError):
        threshold_image(np.zeros((2, 2, 3), dtype=np.uint8), 128)
