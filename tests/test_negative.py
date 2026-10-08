import numpy as np
from model.image_io import load_image, save_image
from model.negative import negative_image


def test_image_negative():
    original = np.array([
        [0,   50,  100],
        [150, 200, 255]
    ], dtype=np.uint8)

    expected = np.array([
        [255, 205, 155],
        [105,  55,   0]
    ], dtype=np.uint8)

    result = negative_image(original)

    print("Imagem original:")
    print(original)

    print("\nResultado obtido:")
    print(result)

    print("\nResultado esperado:")
    print(expected)

    assert np.array_equal(result, expected)

    print("\nTeste passou com sucesso!")

def test_real_image():
    # Carrega sua imagem real
    original = load_image("imagens/GatoHalloween.jpg")

    # Aplica o negativo
    negative = negative_image(original)

    # Salva o resultado 
    save_image(
        negative,
        "imagens/Negativo_da_Img.jpg"
    )

    print("Negativo da imagem real gerado com sucesso!")


test_image_negative()
test_real_image()