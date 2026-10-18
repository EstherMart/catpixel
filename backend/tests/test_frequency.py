import numpy as np
import pytest

from backend.model.frequency import (
    compute_spectrum,
    dft2,
    fft2,
    filter_with_mask,
    idft2,
    ifft2,
    pad_to_power_of_two,
    shift,
    spectrum_image,
    spectrum_shape,
    unshift,
)

RNG = np.random.default_rng(0)
PHOTO = RNG.integers(0, 256, size=(20, 30), dtype=np.uint8)


def test_own_dft_and_fft_match_the_reference_and_invert_exactly():
    square = RNG.integers(0, 256, size=(16, 32)).astype(np.float64)
    odd = RNG.integers(0, 256, size=(9, 12)).astype(np.float64)
    assert np.allclose(fft2(square), np.fft.fft2(square))  # numpy.fft só serve de referência nos testes
    assert np.allclose(dft2(square), np.fft.fft2(square))
    assert np.allclose(dft2(odd), np.fft.fft2(odd))  # a DFT aceita qualquer tamanho
    assert np.allclose(ifft2(fft2(square)).real, square) and np.allclose(idft2(dft2(odd)).real, odd)
    with pytest.raises(ValueError):
        fft2(odd)  # a FFT radix-2 exige potência de 2

    assert np.allclose(shift(np.fft.fft2(square)), np.fft.fftshift(np.fft.fft2(square)))
    assert np.array_equal(unshift(shift(odd)), odd)
    impulse = np.zeros((8, 8))
    impulse[3, 5] = 1  # espectro de um impulso: magnitude constante
    assert np.allclose(np.abs(fft2(impulse)), 1)

    padded = pad_to_power_of_two(PHOTO)
    assert padded.shape == (32, 32) and np.array_equal(padded[:20, :30], PHOTO) and not padded[20:].any()
    assert spectrum_shape((720, 1280), "fft") == (1024, 2048) and spectrum_shape((9, 12), "dft") == (9, 12)
    assert compute_spectrum(PHOTO, "dft").shape == (20, 30) and compute_spectrum(PHOTO, "fft").shape == (32, 32)

    image = spectrum_image(compute_spectrum(PHOTO, "fft"))
    assert image.dtype == np.uint8 and image[16, 16] == 255  # a frequência zero fica no centro e é a mais clara
    for invalid in (lambda: spectrum_shape((10, 10), "xyz"), lambda: spectrum_shape((2000, 20), "dft"),
                    lambda: spectrum_shape((4000, 20), "fft"), lambda: compute_spectrum(np.zeros((2, 2, 3)), "fft")):
        with pytest.raises(ValueError):
            invalid()


def test_filtering_by_a_mask_on_the_spectrum():
    for algorithm in ("fft", "dft"):
        shape = spectrum_shape(PHOTO.shape, algorithm)
        white = np.full(shape, 255, dtype=np.uint8)
        assert np.array_equal(filter_with_mask(PHOTO, white, algorithm), PHOTO)  # máscara branca: imagem igual
        assert filter_with_mask(PHOTO, np.zeros(shape, dtype=np.uint8), algorithm).max() == 0  # preta: tudo zerado

        center = np.zeros(shape, dtype=np.uint8)
        center[shape[0] // 2, shape[1] // 2] = 255  # só a frequência zero: sobra a média, imagem lisa
        flat = filter_with_mask(PHOTO, center, algorithm)
        # a média inclui os zeros do preenchimento da FFT: 600 pixels da imagem entre 1024 do espectro
        expected = PHOTO.mean() * PHOTO.size / (shape[0] * shape[1])
        assert len(np.unique(flat)) == 1 and abs(int(flat[0, 0]) - expected) <= 1

    # passa-baixa (disco branco no centro) borra; ao inverter a máscara, só sobram os detalhes
    stripes = np.tile(np.array([0, 255], dtype=np.uint8), (16, 8))  # frequência mais alta possível
    shape = spectrum_shape(stripes.shape, "fft")
    low_pass = np.zeros(shape, dtype=np.uint8)
    low_pass[shape[0] // 2 - 2:shape[0] // 2 + 3, shape[1] // 2 - 2:shape[1] // 2 + 3] = 255
    assert filter_with_mask(stripes, low_pass, "fft").std() < 5 < stripes.std()
    half = filter_with_mask(PHOTO, np.full((8, 8), 255, dtype=np.uint8), "fft")  # máscara de outro tamanho é redimensionada
    assert np.array_equal(half, PHOTO)
    assert filter_with_mask(PHOTO, 255 - low_pass[:32, :32], "fft", normalize=True).max() == 255
    with pytest.raises(ValueError):
        filter_with_mask(PHOTO, np.zeros((4, 4, 3), dtype=np.uint8))
