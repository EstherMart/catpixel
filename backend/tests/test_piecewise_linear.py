import numpy as np
import pytest

from backend.model.piecewise_linear import build_piecewise_lut, piecewise_linear

RAMP = np.arange(256, dtype=np.uint8).reshape(16, 16)


def test_points_on_the_diagonal_keep_the_image():
    assert np.array_equal(piecewise_linear(RAMP, 85, 85, 170, 170), RAMP)


def test_contrast_stretch_passes_through_the_given_points():
    lut = build_piecewise_lut([(50, 10), (200, 240)])
    assert (lut[0], lut[50], lut[200], lut[255]) == (0, 10, 240, 255)
    assert lut[125] == 125  # meio do trecho (50,10)-(200,240)


def test_step_between_equal_r_values_works_like_a_threshold():
    lut = build_piecewise_lut([(128, 0), (128, 255)])
    assert (lut[127], lut[128], lut[129]) == (0, 0, 255)


def test_extreme_points_do_not_divide_by_zero():
    lut = build_piecewise_lut([(0, 50), (255, 200)])
    assert len(lut) == 256
    assert all(0 <= value <= 255 for value in lut)


def test_points_out_of_order_are_sorted():
    assert build_piecewise_lut([(200, 240), (50, 10)]) == build_piecewise_lut([(50, 10), (200, 240)])


@pytest.mark.parametrize("point", [(-1, 0), (0, 256), (300, 10)])
def test_rejects_points_out_of_range(point):
    with pytest.raises(ValueError):
        build_piecewise_lut([point])


def test_does_not_change_the_input():
    matrix = np.array([[100]], dtype=np.uint8)
    piecewise_linear(matrix, 50, 0, 200, 255)
    assert matrix[0, 0] == 100
