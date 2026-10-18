import numpy as np
import pytest

from backend.model.brightness import adjust_brightness
from backend.model.gamma_log import gamma_correction, log_transformation
from backend.model.negative import negative_image
from backend.model.piecewise_linear import build_piecewise_lut, piecewise_linear
from backend.model.thresholding import threshold_image

RAMP = np.arange(256, dtype=np.uint8).reshape(16, 16)
COLOR = np.zeros((2, 2, 3), dtype=np.uint8)


def test_threshold_and_negative():
    matrix = np.array([[10, 127, 128], [200, 0, 255]], dtype=np.uint8)
    assert threshold_image(matrix, 128).tolist() == [[0, 0, 255], [255, 0, 255]]
    assert negative_image(matrix).tolist() == [[245, 128, 127], [55, 255, 0]]
    assert np.array_equal(negative_image(negative_image(RAMP)), RAMP)  # negativo duas vezes = original
    assert matrix[0, 0] == 10  # a entrada não muda
    for invalid in (lambda: threshold_image(matrix, 256), lambda: threshold_image(matrix, -1),
                    lambda: threshold_image(COLOR, 1), lambda: negative_image(COLOR)):
        with pytest.raises(ValueError):
            invalid()


def test_brightness_gamma_and_log():
    assert np.array_equal(adjust_brightness(RAMP, 1), RAMP)
    assert not adjust_brightness(RAMP, 0).any()
    assert adjust_brightness(np.array([[100, 200]], dtype=np.uint8), 2).tolist() == [[200, 255]]  # satura em 255

    assert np.array_equal(gamma_correction(RAMP, 1), RAMP)
    assert int(gamma_correction(RAMP, 0.5)[8, 0]) > 128 > int(gamma_correction(RAMP, 2)[8, 0])
    gamma = gamma_correction(RAMP, 2.2)
    assert gamma[0, 0] == 0 and gamma[15, 15] == 255  # extremos fixos

    log = log_transformation(RAMP)
    assert log[0, 0] == 0 and log[15, 15] == 255 and int(log[8, 0]) > 128

    for invalid in (lambda: adjust_brightness(RAMP, -1), lambda: adjust_brightness(RAMP, float("nan")),
                    lambda: gamma_correction(RAMP, 0), lambda: gamma_correction(RAMP, float("inf"))):
        with pytest.raises(ValueError):
            invalid()


def test_piecewise_linear():
    assert np.array_equal(piecewise_linear(RAMP, 85, 85, 170, 170), RAMP)  # pontos na diagonal não mudam a imagem

    lut = build_piecewise_lut([(50, 10), (200, 240)])
    assert (lut[0], lut[50], lut[125], lut[200], lut[255]) == (0, 10, 125, 240, 255)
    assert build_piecewise_lut([(200, 240), (50, 10)]) == lut  # pontos fora de ordem são ordenados

    step = build_piecewise_lut([(128, 0), (128, 255)])
    assert (step[127], step[128], step[129]) == (0, 0, 255)  # degrau
    assert len(build_piecewise_lut([(0, 50), (255, 200)])) == 256  # extremos sem divisão por zero

    with pytest.raises(ValueError):
        build_piecewise_lut([(300, 10)])
