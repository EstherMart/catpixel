<p align="center">
  <img src="assets/LogoPNG.png" alt="Logo do CatPixel" width="200">
</p>

<h1 align="center">CatPixel</h1>

<p align="center">
  Editor de imagens com interface web, feito para estudar processamento de imagens.<br>
  Os algoritmos são escritos do zero em Python (NumPy), manipulando diretamente a matriz da imagem.
</p>

## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Como rodar](#como-rodar)
- [Usando a interface](#usando-a-interface)
- [Usando os algoritmos sem a interface](#usando-os-algoritmos-sem-a-interface)
- [Testes](#testes)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Princípios do projeto](#princípios-do-projeto)
- [Documentação e contribuição](#documentação-e-contribuição)

## Sobre o projeto

O CatPixel nasceu como trabalho da disciplina de Processamento de Imagens. A ideia é ter um programa com interface simples, para que uma pessoa sem experiência edite imagens salvas no próprio computador, e ao mesmo tempo código legível, onde cada técnica clássica aparece escrita de forma direta, sem biblioteca de processamento de imagens.

Ele abre e salva imagens BMP, JPG e PNG, em tons de cinza ou coloridas. A interface roda no navegador, e o servidor (FastAPI) roda na sua máquina.

## Funcionalidades

Operações pontuais

- Limiarização, negativo, brilho, potência (correção de gama), logaritmo e função linear definida por partes.
- Exibição do histograma e equalização de histograma.
- Esteganografia: esconde e revela um texto nos bits menos significativos dos pixels.

Filtros espaciais

- Convolução com filtro quadrado de dimensão ímpar (de 3x3 até 11x11), com grade de valores editável, modelos prontos e divisor.
- Suavização pela média e gaussiana (média ponderada), filtro da mediana.
- Aguçamento por Laplaciano e por high-boost.

Transformações geométricas

- Escala e rotação, com interpolação pelo vizinho mais próximo ou bilinear.
- Rotação em torno de um pivô escolhido.

Domínio da frequência

- Transformada discreta de Fourier (DFT) e transformada rápida (FFT radix-2), ambas implementadas no projeto, sem `numpy.fft`.
- Espectro deslocado na tela, com um pincel (preto, branco ou cinza, duro ou suave) para editá-lo, e transformada inversa para obter a imagem filtrada.

Imagens coloridas

- Conversão RGB para HSI (e de volta) e escala de cinza por média simples ou ponderada.
- Negativo colorido, sépia, chroma-key (com a distância da cor e a imagem de fundo ajustáveis).
- Ajuste de matiz, saturação e brilho, e ajuste de canal (ciano/vermelho, magenta/verde, amarelo/azul).
- Histogramas de R, G, B e intensidade, e equalização de histograma pelo componente de intensidade (HSI).
- Todos os processamentos de tons de cinza também funcionam em imagens coloridas.

Interface

- Pré-visualização ao vivo enquanto os controles são ajustados, histórico com desfazer e refazer, comparação com a original, zoom e arrastar, e histograma sempre visível.

Ainda não estão implementados o filtro de Sobel (X e Y) e a magnitude do gradiente.

## Como rodar

Pré-requisitos: Python 3.10 ou superior e um navegador moderno (Chrome, Firefox ou Edge).

```bash
git clone https://github.com/EstherMart/catpixel.git
cd catpixel

python3 -m venv .venv
source .venv/bin/activate          # no Windows: .venv\Scripts\activate
pip install -r requirements/requirements.txt

uvicorn backend.app:app --reload --port 8765
```

Abra <http://localhost:8765> no navegador. Para parar o servidor, use `Ctrl+C`. Nas próximas vezes, basta ativar o ambiente e rodar o `uvicorn`.

As dependências são `numpy`, `Pillow` (só para abrir e salvar arquivos), `FastAPI`, `uvicorn` e `python-multipart`.

## Usando a interface

1. Clique em **Abrir imagem** ou arraste um arquivo para a janela. A pasta [imagens/](imagens/) tem fotos de exemplo.
2. Clique em um botão da barra superior (**Ajustes**, **Filtros**, **Geometria**, **Frequência**, **Cores** ou **Esteganografia**). A lista das operações dele aparece no painel **Parâmetros**, à direita.
3. Escolha uma operação e mexa nos controles dela: a pré-visualização muda na hora. Clique em **Aplicar** para gravar a edição no histórico, ou em **Cancelar** para voltar à lista.
4. Use **Ver original** para comparar, o painel **Histórico** (ou Ctrl+Z e Ctrl+Shift+Z) para desfazer e refazer, e o menu **Arquivo** para salvar em BMP ou JPG.
5. A roda do mouse dá zoom, arrastar move a imagem e o duplo clique ajusta à tela.

Dicas:

- Prefira salvar em BMP. O JPG comprime com perdas, o que cria tons de cinza nas bordas de imagens binárias e apaga mensagens escondidas pela esteganografia.
- Editar o espectro: abra **Frequência**, escolha **Espectro de Fourier** e pinte sobre ele. Preto elimina as frequências pintadas, branco as mantém e cinza as atenua. **Aplicar filtro** calcula a transformada inversa. O botão do meio do mouse move a imagem enquanto você pinta.
- O servidor guarda uma única imagem em edição, pensada para uso local por uma pessoa.

A documentação automática da API fica em <http://localhost:8765/docs>.

## Usando os algoritmos sem a interface

Os algoritmos de `backend/model/` não dependem da parte web e trabalham com matrizes NumPy `uint8`: `(altura, largura)` para tons de cinza e `(altura, largura, 3)` em R, G, B para imagens coloridas.

```python
from backend.model.image_io import load_image, save_image
from backend.model.spatial_filters import median_filter
from backend.model.thresholding import threshold_image

imagem = load_image("imagens/GatoHalloween.jpg")        # colorida: (H, W, 3)
cinza = imagem.mean(axis=2).astype("uint8")             # ou use backend.model.color.to_grayscale
suave = median_filter(cinza, 5)                         # mediana com vizinhança 5x5
binaria = threshold_image(suave, 128)                   # pixels >= 128 viram 255, os demais 0
save_image(binaria, "saida.bmp")
```

As funções de tons de cinza recebem uma matriz 2D. Para aplicar uma delas a uma imagem colorida, rode-a em cada canal, como a interface faz.

## Testes

```bash
pip install -r requirements/requirements-dev.txt
python -m pytest
```

A suíte é pequena e roda em poucos segundos. Cada teste cobre uma funcionalidade e reúne várias verificações.

## Estrutura do projeto

```
catpixel/
├── backend/                      # Python
│   ├── app.py                    # rotas FastAPI e entrega do front-end
│   ├── operations.py             # catálogo de operações que a interface pode pedir
│   ├── session.py                # imagem aberta e histórico (desfazer/refazer)
│   ├── model/                    # algoritmos, sem nada de web
│   │   ├── image_io.py           # abrir, salvar e codificar imagens
│   │   ├── sampling.py           # redução para a pré-visualização
│   │   ├── thresholding.py       # limiarização
│   │   ├── negative.py           # negativo
│   │   ├── brightness.py         # brilho
│   │   ├── gamma_log.py          # potência (gama) e logaritmo
│   │   ├── piecewise_linear.py   # linear definida por partes
│   │   ├── histogram.py          # histograma e equalização
│   │   ├── convolution.py        # convolução com filtro quadrado ímpar
│   │   ├── spatial_filters.py    # média, gaussiana, mediana, Laplaciano e high-boost
│   │   ├── geometry.py           # escala e rotação (com pivô) com interpolação
│   │   ├── frequency.py          # DFT, FFT, espectro deslocado e filtro por máscara
│   │   ├── color.py              # HSI, escala de cinza, ajustes de cor, sépia e chroma-key
│   │   ├── steganography.py      # esconder e revelar texto (LSB)
│   │   └── utils/lut.py          # aplica uma tabela de 256 tons à imagem
│   └── tests/
├── frontend/                     # HTML, CSS e JavaScript puros
│   ├── index.html
│   ├── css/styles.css            # tema azul-escuro e verde
│   └── js/
│       ├── main.js               # liga tudo
│       ├── api.js                # chamadas à API
│       ├── stage-view.js         # área da imagem: zoom e arrastar
│       ├── adjustments-panel.js  # lista de operações e painel de parâmetros
│       ├── controls.js           # controles (slider, texto, lista, grade do filtro, espectro, cor, arquivo)
│       ├── histogram-panel.js    # gráfico do histograma
│       ├── history-panel.js      # histórico
│       ├── menubar.js            # barra superior
│       └── toast.js              # avisos
├── docs/                         # como cada funcionalidade foi feita
├── requirements/
├── imagens/                      # imagens de exemplo
└── assets/                       # logos
```

## Princípios do projeto

- Os algoritmos são escritos no projeto e manipulam a matriz da imagem diretamente. Não se usa biblioteca de processamento de imagens nem funções prontas que façam a própria técnica (convolução, FFT, interpolação etc.).
- O Pillow só abre e salva arquivos, em `backend/model/image_io.py`. O NumPy serve para álgebra e operações em bloco sobre matrizes. O `numpy.fft` aparece apenas nos testes, como referência para conferir a DFT e a FFT próprias.
- O código em `backend/model/` não importa nada de web, e cada operação nova é registrada em um único catálogo (`backend/operations.py`).
- Filtros que geram valores negativos ou acima de 255 (como o Laplaciano) têm o resultado normalizado apenas para exibição.
