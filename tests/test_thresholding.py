import numpy as np
from model.image_io import load_image, save_image
from model.thresholding import threshold_image


test_matrix = np.array([[ 10, 127, 128],
                        [200,   0, 255]], dtype=np.uint8)

result = threshold_image(test_matrix, 128)

expected = np.array([[  0,   0, 255],
                     [255,   0, 255]], dtype=np.uint8)

print("Resultado:")
print(result)

assert np.array_equal(result, expected), "A limiarização não deu o resultado esperado!"
print("Teste da matriz pequena confere\n")



real_image = load_image("imagens/GatoHalloween.jpg")   
print("Imagem carregada, formato (altura, largura):", real_image.shape)

for threshold in (64, 128, 192):
    binary_image = threshold_image(real_image, threshold)

    # Só podem existir os valores 0 e 255 na saída
    print(f"Limiar {threshold}: valores presentes ->", np.unique(binary_image))

    # Salva em BMP: o JPG comprime com perdas e criaria tons de cinza nas bordas
    save_image(binary_image, f"imagens/Imagem_Limiarizacao_{threshold}.bmp")

print("Imagens com os thresholds definidos geradas com sucesso")