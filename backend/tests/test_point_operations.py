import numpy as np
import pytest

from backend.model.brightness import adjust_brightness
from backend.model.gamma_log import gamma_correction, log_transformation
from backend.model.negative import negative_image

RAMP = np.arange(256, dtype=np.uint8).reshape(16, 16)


def test_negative_gives_the_expected_result():
    matrix = np.array([[0, 100], [255, 1]], dtype=np.uint8)
    assert np.array_equal(negative_image(matrix), np.array([[255, 155], [0, 254]], dtype=np.uint8))


def test_negative_twice_gives_back_the_original():
    assert np.array_equal(negative_image(negative_image(RAMP)), RAMP)


def test_negative_does_not_change_the_input():
    matrix = np.array([[10]], dtype=np.uint8)
    negative_image(matrix)
    assert matrix[0, 0] == 10


def test_negative_rejects_color_image():
    with pytest.raises(ValueError):
        negative_image(np.zeros((2, 2, 3), dtype=np.uint8))


def test_brightness_one_keeps_the_image():
    assert np.array_equal(adjust_brightness(RAMP, 1), RAMP)


def test_brightness_zero_gives_black():
    assert not adjust_brightness(RAMP, 0).any()


def test_brightness_saturates_at_255():
    result = adjust_brightness(np.array([[100, 200]], dtype=np.uint8), 2)
    assert result.tolist() == [[200, 255]]


@pytest.mark.parametrize("factor", [-1, float("nan"), float("inf")])
def test_brightness_rejects_invalid_factor(factor):
    with pytest.raises(ValueError):
        adjust_brightness(RAMP, factor)


def test_gamma_one_keeps_the_image():
    assert np.array_equal(gamma_correction(RAMP, 1), RAMP)


def test_gamma_below_one_brightens_and_above_one_darkens():
    assert int(gamma_correction(RAMP, 0.5)[8, 0]) > 128
    assert int(gamma_correction(RAMP, 2)[8, 0]) < 128


def test_gamma_keeps_black_and_white():
    result = gamma_correction(RAMP, 2.2)
    assert result[0, 0] == 0 and result[15, 15] == 255


@pytest.mark.parametrize("gamma", [0, -1, float("nan")])
def test_gamma_rejects_invalid_value(gamma):
    with pytest.raises(ValueError):
        gamma_correction(RAMP, gamma)


def test_log_keeps_black_and_white_and_brightens_the_middle():
    result = log_transformation(RAMP)
    assert result[0, 0] == 0 and result[15, 15] == 255
    assert int(result[8, 0]) > 128
