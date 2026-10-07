# Usando o Pillow apenas para ações de entrada e saída (I/O)
import numpy as np
from PIL import Image

# Vamos ler um arquivo de imagem e transformar em uma matriz numpy
# Imagem é uma grade de pixels, podemos representar por uma matriz, M x N, onde 0 fica no canto superior esquerdo
# Em imagens preto e branco, cada pixel vai ter uma cor, essa cor é um valor no range de 0(preto) a 255(branco)
# Então, podemos representar com uma matriz onde cada valor é a cor do pixel e as coordenadas de um pixel é (x,y) 
# Recebe o caminho/path do arquivo (str) e devolve um np.ndaaray
def load_image(path: str) -> np.ndarray:
    """Lê um arquivo e devolve uma matriz 2D uint8 de formato (H, W)."""
    with Image.open(path) as img:
        # Arquivos podem vir em modos diferentes (L, P, RGBA...).
        # Normalizamos para RGB para o resto do programa lidar com um só formato.
        img = img.convert("L") # O parâmetro L devolve uma imagem em escala de cinza, então temos uma matriz 2D em vez da (H,W,3)
        return np.array(img, dtype=np.uint8)   # np.array copia; np.asarray poderia devolver somente leitura

# Vamos pegar a matriz e transformar/gravar de volta em imagem
def save_image(matrix: np.ndarray, path: str) -> None:
    """Grava uma matriz como imagem em BMP/JPG, conforme a extensão."""
    matrix = np.clip(matrix, 0, 255).astype(np.uint8)
    Image.fromarray(matrix).save(path)