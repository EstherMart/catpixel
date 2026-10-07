from model.image_io import load_image, save_image

img = load_image("imagens/GatoHalloween.jpg")
print(img.shape, img.dtype)
save_image(img, "imagens/copia.bmp")