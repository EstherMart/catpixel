
import numpy as np
from model.image_io import load_image, save_image
from model.brightness import (
    build_brightness_lut,
    build_gamma_lut,
    build_log_lut,
    mean_brightness,
    apply_lut,
)


def test_image_brightness():
    original = np.array([
        [0,   50, 100],
        [150, 200, 255]
    ], dtype=np.uint8)

    expected = np.array([
        [50, 100, 150],
        [200, 250, 255]
    ], dtype=np.uint8)

    result = apply_lut(original, build_brightness_lut(50))

    print("Imagem original:")
    print(original)

    print("\nResultado obtido (brilho +50):")
    print(result)

    print("\nResultado esperado:")
    print(expected)

    assert np.array_equal(result, expected)
    assert np.isclose(mean_brightness(original), np.mean(original))
    assert build_gamma_lut(1) == list(range(256))
    assert build_log_lut()[0] == 0
    assert build_log_lut()[255] == 255

    print("\nTeste passou com sucesso!\n")


def test_real_image():
    original = load_image("imagens/GatoHalloween.jpg")

    # Ajustes de brilho (altere os valores para experimentar)
    for brightness in (50, -50):
        result = apply_lut(original, build_brightness_lut(brightness))
        save_image(result, f"imagens/Brilho_{brightness:+d}.png")

    # Transformações gama
    for gamma in (0.5, 2.0):
        result = apply_lut(original, build_gamma_lut(gamma))
        save_image(result, f"imagens/BrilhoTest_Gama_{str(gamma).replace('.', '_')}.png")

    # Transformação logarítmica
    result = apply_lut(original, build_log_lut())
    save_image(result, "imagens/BrilhoTest_Logaritmo.png")

    print("Imagens processadas e salvas com sucesso!")


test_image_brightness()
test_real_image()
