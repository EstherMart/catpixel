import base64
import io

import numpy as np
import pytest
from PIL import Image

from backend.model.color import (
    adjust_channels,
    adjust_hsi,
    channel_histograms,
    chroma_key,
    equalize_intensity,
    hsi_component,
    hsi_to_rgb,
    intensity,
    rgb_to_hsi,
    sepia,
    to_grayscale,
)
from backend.operations import run_operation

RNG = np.random.default_rng(11)
PHOTO = RNG.integers(0, 256, size=(24, 32, 3), dtype=np.uint8)
RED = np.array([[[255, 0, 0]]], dtype=np.uint8)


def test_hsi_conversion_grayscale_component_views_histograms_and_equalization():
    primaries = np.array([[[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 255, 255], [0, 0, 0]]], dtype=np.uint8)
    hue, saturation, brightness = rgb_to_hsi(primaries)
    assert np.allclose(hue[0, :4], [0, 120, 240, 60]) and np.allclose(saturation[0], [1, 1, 1, 1, 0, 0])
    assert np.allclose(brightness[0, :3], 1 / 3) and brightness[0, 4] == 1  # branco e preto não geram divisão por zero
    assert np.abs(hsi_to_rgb(*rgb_to_hsi(PHOTO)).astype(int) - PHOTO).max() <= 1  # ida e volta
    assert np.array_equal(hsi_to_rgb(np.array([370.0]), np.array([1.0]), np.array([0.4])),
                          hsi_to_rgb(np.array([10.0]), np.array([1.0]), np.array([0.4])))  # o matiz dá a volta

    assert to_grayscale(RED).tolist() == [[85]] and to_grayscale(RED, weighted=True).tolist() == [[76]]  # média simples e ponderada
    assert to_grayscale(PHOTO).shape == (24, 32) and np.array_equal(to_grayscale(PHOTO[:, :, 0]), PHOTO[:, :, 0])
    green = np.array([[[0, 255, 0]]], dtype=np.uint8)
    assert hsi_component(green, "hue").tolist() == [[85]] and hsi_component(RED, "saturation").tolist() == [[255]]
    assert hsi_component(PHOTO, "intensity").shape == (24, 32)

    counts = channel_histograms(PHOTO)
    assert set(counts) == {"r", "g", "b", "i"} and all(sum(c) == PHOTO.shape[0] * PHOTO.shape[1] for c in counts.values())
    assert counts["r"][int(PHOTO[0, 0, 0])] >= 1 and set(channel_histograms(PHOTO[:, :, 0])) == {"i"}

    dull = (100 + RNG.integers(0, 40, size=(30, 30, 3))).astype(np.uint8)  # cores pouco contrastadas
    spread = equalize_intensity(dull)
    assert np.ptp(intensity(spread).astype(int)) > np.ptp(intensity(dull).astype(int))  # só a intensidade foi espalhada
    assert spread.shape == dull.shape


def test_hsi_and_channel_adjustments_sepia_and_chroma_key():
    assert np.array_equal(adjust_hsi(RED, 0, 1, 1), RED)
    assert adjust_hsi(RED, 120, 1, 1).tolist() == [[[0, 255, 0]]]  # vermelho + 120° de matiz = verde
    assert adjust_hsi(RED, 0, 0, 1).tolist() == [[[85, 85, 85]]]  # saturação 0 = cinza
    assert not adjust_hsi(RED, 0, 1, 0).any()
    assert adjust_hsi(PHOTO[:, :, 0], 40, 2, 1).shape == (24, 32, 3)  # cinza vira colorida para o ajuste

    black, white = np.zeros((1, 1, 3), dtype=np.uint8), np.full((1, 1, 3), 255, dtype=np.uint8)
    assert adjust_channels(black, 100, 0, 0).tolist() == [[[255, 0, 0]]]
    assert adjust_channels(white, -100, 0, 0).tolist() == [[[0, 255, 255]]]  # menos vermelho = mais ciano
    assert adjust_channels(white, 0, 0, -100).tolist() == [[[255, 255, 0]]]  # menos azul = mais amarelo
    assert np.array_equal(adjust_channels(PHOTO, 0, 0, 0), PHOTO)

    assert sepia(white).tolist() == [[[255, 255, 239]]] and not sepia(black).any()
    warm = sepia(np.full((1, 1, 3), 128, dtype=np.uint8))[0, 0]
    assert warm[0] > warm[1] > warm[2] and sepia(PHOTO[:, :, 0]).shape == (24, 32, 3)

    screen = np.zeros((4, 6, 3), dtype=np.uint8)
    screen[:, :3] = (0, 255, 0)
    screen[:, 3:] = (200, 0, 0)
    screen[0, 0] = (0, 250, 0)  # verde um pouco diferente
    scenery = np.full((2, 3, 3), (0, 0, 255), dtype=np.uint8)  # outro tamanho: é esticado
    keyed = chroma_key(screen, scenery, (0, 255, 0), 10)
    assert (keyed[:, :3] == (0, 0, 255)).all() and np.array_equal(keyed[:, 3:], screen[:, 3:])
    assert chroma_key(screen, scenery, (0, 255, 0), 0)[0, 0].tolist() == [0, 250, 0]  # distância 0: só o verde exato
    assert not chroma_key(screen, None, (0, 255, 0), 10)[:, :3].any()  # sem fundo, fica preto

    for invalid in (lambda: chroma_key(screen, None, (0, 255, 0), 500), lambda: chroma_key(screen, None, (0, 300, 0), 10),
                    lambda: adjust_hsi(RED, 0, -1, 1), lambda: adjust_channels(RED, 101, 0, 0)):
        with pytest.raises(ValueError):
            invalid()


def test_gray_operations_work_on_color_images_and_color_operations_on_gray_ones():
    kernel = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
    same_size = (
        ("threshold", {"limit": 128}), ("negative", {}), ("brightness", {"factor": 1.5}), ("gamma", {"gamma": 0.5}),
        ("log", {}), ("piecewise", {"r1": 50, "s1": 10, "r2": 200, "s2": 240}), ("mean", {"size": 3}),
        ("gaussian", {"size": 3}), ("median", {"size": 3}), ("laplacian", {"diagonals": 0, "sharpen": 1}),
        ("highboost", {"size": 3, "k": 2, "gaussian": 0}), ("convolution", {"kernel": kernel, "divisor": 1, "normalize": 0}),
        ("rotate_pivot", {"angle": 20, "pivot_x": 50, "pivot_y": 50, "method": 1}), ("equalize", {}),
    )
    for op, params in same_size:
        _, result = run_operation(op, PHOTO, params)
        assert result.shape == PHOTO.shape and result.dtype == np.uint8, op
    for op, params in (("negative", {}), ("median", {"size": 3}), ("gamma", {"gamma": 0.5})):  # canal a canal = o mesmo que em cinza
        assert np.array_equal(run_operation(op, PHOTO, params)[1][:, :, 1], run_operation(op, PHOTO[:, :, 1], params)[1])
    assert np.array_equal(run_operation("negative", PHOTO, {})[1], 255 - PHOTO)  # negativo colorido

    assert run_operation("scale", PHOTO, {"scale_x": 2, "scale_y": 3, "method": 0})[1].shape == (72, 64, 3)
    assert run_operation("rotate", PHOTO, {"angle": 90, "expand": 1, "method": 1})[1].shape == (32, 24, 3)
    assert run_operation("grayscale", PHOTO, {"weighted": 1})[1].shape == (24, 32)  # a conversão devolve imagem em cinza
    assert run_operation("hsi_component", PHOTO, {"component": 0})[1].shape == (24, 32)

    secret = "Olá, cores!"
    hidden = run_operation("hide_message", PHOTO, {"text": secret})[1]
    assert hidden.shape == PHOTO.shape and np.abs(hidden.astype(int) - PHOTO).max() <= 1  # três bits por pixel
    assert run_operation("hide_message", PHOTO[:, :, 0], {"text": secret})[1].shape == (24, 32)

    small = PHOTO[:8, :8]
    buffer = io.BytesIO()
    Image.fromarray(np.full((8, 8), 255, dtype=np.uint8)).save(buffer, format="PNG")
    white_mask = base64.b64encode(buffer.getvalue()).decode()
    filtered = run_operation("frequency_filter", small, {"mask": white_mask, "algorithm": 0, "normalize": 0})[1]
    assert np.array_equal(filtered, small)  # espectro sem edição devolve a imagem, em cada canal

    gray = PHOTO[:, :, 0]
    for op, params in (("sepia", {}), ("hsi_adjust", {"hue": 30, "saturation": 1, "intensity": 1}),
                       ("channel_adjust", {"cyan_red": 10, "magenta_green": 0, "yellow_blue": -10}),
                       ("chroma_key", {"key_r": 0, "key_g": 255, "key_b": 0, "distance": 100})):
        assert run_operation(op, gray, params)[1].shape == (24, 32, 3), op  # imagem em cinza é promovida a colorida
