# Como cada funcionalidade foi implementada

Cada funcionalidade responde a três perguntas:

- **O quê:** o que ela faz, com a fórmula ou a regra.
- **Por quê:** a razão de existir e as decisões de projeto.
- **Como:** o algoritmo, os arquivos e os parâmetros.

Ao terminar uma funcionalidade, troque o aviso "Ainda não implementado" pelo texto dela e marque ✅ na tabela de [Funcionalidades](../README.md#funcionalidades). Os passos para criar uma funcionalidade estão em [novas-funcionalidades.md](novas-funcionalidades.md).

## Base

### Abrir e salvar imagens

- **O quê:** abre arquivos BMP, JPG e PNG e salva em BMP ou JPG.
- **Por quê:** o enunciado exige abrir e salvar nesses formatos e permite biblioteca de terceiros só para isso. O BMP é o formato preferido para salvar, porque o JPG comprime com perdas e cria tons de cinza nas bordas de imagens binárias.
- **Como:**
  - `backend/model/image_io.py`: `load_image` usa o Pillow para ler o arquivo e converte para uma matriz numpy `uint8` de formato (altura, largura) em escala de cinza. `encode_image` faz o caminho contrário.
  - `backend/app.py`: `POST /api/open` recebe o arquivo, e `GET /api/save?format=bmp|jpg` devolve o arquivo para download.
- **Limitação:** tudo é convertido para escala de cinza. Isso precisa mudar para a parte colorida.

## Operações pontuais

### Limiarização

- **O quê:** transforma a imagem em preto e branco a partir de um limiar `T` entre 0 e 255:
  - intensidade `>= T` vira 255 (branco);
  - intensidade `< T` vira 0 (preto).
- **Por quê:** é a operação mais simples de segmentação e separa o objeto do fundo. Usei `>=` (e não `>`) porque o enunciado trata o limiar como o primeiro valor que fica branco. O resultado é uma imagem nova, e a original não muda, o que permite desfazer.
- **Como:**
  - Algoritmo, em `backend/model/thresholding.py`, função `threshold_image(matrix, threshold)`:
    1. valida que a matriz é 2D e que `0 <= T <= 255` (senão lança `ValueError`);
    2. cria uma matriz de zeros do mesmo tamanho;
    3. percorre cada pixel `(y, x)` e escreve 255 onde a intensidade é `>= T`.
  - O laço é feito pixel a pixel, de propósito: o trabalho exige manipular a matriz diretamente. Ele é lento em imagens grandes, e uma versão vetorizada do numpy pode substituí-lo depois.
  - Ligação com a interface:
    - `backend/operations.py`: operação `"threshold"`, com o parâmetro inteiro `limit`.
    - `frontend/js/adjustments-panel.js`: entrada `threshold` em `ADJUSTMENTS`, com um slider de 0 a 255 (padrão 128).
  - Fluxo: o slider chama `POST /api/preview` (roda numa versão reduzida da imagem, de até 640 px, só para mostrar). Ao clicar em **Aplicar**, `POST /api/apply` roda na imagem inteira e grava um passo no histórico.

### Negativo

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Brilho

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Potência (correção de gama)

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Linear definida por partes

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Esteganografia

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

## Histograma e convolução

### Exibição do histograma

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Equalização de histograma

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Filtro genérico por convolução

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

## Filtros espaciais

### Suavização pela média (simples)

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Suavização Gaussiana (média ponderada)

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Filtro da mediana

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Aguçamento por Laplaciano

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Aguçamento High-Boost

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Sobel X e Y

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Magnitude do gradiente

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

## Transformações geométricas

### Escala (vizinho mais próximo e bilinear)

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Rotação (vizinho mais próximo e bilinear)

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Rotação com pivô

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

## Domínio da frequência

### Transformada Discreta de Fourier

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Transformada Rápida de Fourier (FFT)

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Espectro deslocado com edição pelo usuário

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Transformada inversa

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

## Imagens coloridas

### Conversão RGB ↔ HSI

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Escala de cinza (média simples e ponderada)

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Negativo colorido

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Chroma-Key

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Histogramas R, G, B e I

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Equalização de histograma colorida (HSI)

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Ajuste de matiz, saturação e brilho

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Ajuste de canal (C/R, M/G, Y/B)

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**

### Sépia

> ⬜ Ainda não implementado.

- **O quê:**
- **Por quê:**
- **Como:**
