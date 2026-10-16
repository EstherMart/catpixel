<p align="center">
  <img src="assets/LogoPNG.png" alt="Logo do CatPixel" width="200">
</p>

<h1 align="center">CatPixel</h1>

<p align="center">
  Processador de imagens com interface web: front-end em JavaScript e algoritmos em Python (FastAPI).<br>
  Todos os algoritmos são implementados do zero, manipulando diretamente a matriz da imagem.
</p>

> **Status:** em desenvolvimento. A leitura/gravação de imagens, as operações pontuais (limiarização, negativo, brilho, gama, logaritmo, linear por partes), a esteganografia e a interface web (menus, zoom, histórico, desfazer/refazer) estão prontas. Os demais algoritmos ainda não foram implementados (veja o [Roadmap](#roadmap)).

## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [Como rodar](#como-rodar)
- [Funcionalidades](#funcionalidades)
- [Roadmap](#roadmap)
- [Primeiros passos](#primeiros-passos)
- [Uso](#uso)
- [Testes](#testes)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Regras do projeto](#regras-do-projeto)
- [Contribuindo](#contribuindo)
- [Licença](#licença)

## Sobre o projeto

O CatPixel é um trabalho da disciplina de Processamento de Imagens. O objetivo é um programa com interface gráfica simples, para que uma pessoa sem experiência edite imagens salvas no próprio computador.

## Como rodar

Na raiz do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate          # no Windows: .venv\Scripts\activate
pip install -r requirements/requirements.txt
uvicorn backend.app:app --reload --port 8765
```

Abra <http://localhost:8765> no navegador. Para parar o servidor, use `Ctrl+C`. Nas próximas vezes, basta ativar o ambiente (`source .venv/bin/activate`) e rodar o `uvicorn`.

## Funcionalidades

Legenda: ✅ pronto · 🚧 em andamento · ⬜ pendente

### Base

| Funcionalidade            | Status |
| ------------------------- | ------ |
| Abrir imagens (BMP, JPG)  | ✅     |
| Salvar imagens (BMP, JPG) | ✅     |
| Interface gráfica (web)   | ✅     |

### Trabalho 1 — Operações pontuais, histograma e convolução

| Funcionalidade                                                                      | Status |
| ----------------------------------------------------------------------------------- | ------ |
| Limiarização                                                                        | ✅     |
| Negativo                                                                            | ✅     |
| Brilho                                                                              | ✅     |
| Potência (correção de gama) e logaritmo                                             | ✅     |
| Linear definida por partes                                                          | ✅     |
| Esteganografia                                                                      | ✅     |
| Exibição do histograma                                                              | ⬜     |
| Equalização de histograma                                                           | ⬜     |
| Filtro genérico por convolução (3x3 até, no mínimo, 9x9, mesmo tamanho da original) | ⬜     |

### Filtros espaciais

| Funcionalidade                                        | Status |
| ----------------------------------------------------- | ------ |
| Suavização pela média (simples e ponderada/Gaussiana) | ⬜     |
| Filtro da mediana                                     | ⬜     |
| Aguçamento por Laplaciano                             | ⬜     |
| Aguçamento High-Boost                                 | ⬜     |
| Sobel X e Y (com normalização para exibição)          | ⬜     |
| Detecção de bordas pela magnitude do gradiente        | ⬜     |

### Transformações geométricas

| Funcionalidade                            | Status |
| ----------------------------------------- | ------ |
| Escala (vizinho mais próximo e bilinear)  | ⬜     |
| Rotação (vizinho mais próximo e bilinear) | ⬜     |
| Rotação com pivô especificado             | ⬜     |

### Domínio da frequência

| Funcionalidade                                                            | Status |
| ------------------------------------------------------------------------- | ------ |
| Transformada Discreta de Fourier (própria)                                | ⬜     |
| Transformada Rápida (FFT)                                                 | ⬜     |
| Espectro deslocado com edição pelo usuário (pincel preto, branco e suave) | ⬜     |
| Transformada inversa a partir do espectro editado                         | ⬜     |

### Imagens coloridas

| Funcionalidade                                                     | Status |
| ------------------------------------------------------------------ | ------ |
| Conversão RGB ↔ HSI                                                | ⬜     |
| Escala de cinza (média simples e ponderada)                        | ⬜     |
| Negativo colorido                                                  | ⬜     |
| Chroma-Key (distância da cor verde e imagem substituta ajustáveis) | ⬜     |
| Histogramas R, G, B e I                                            | ⬜     |
| Equalização de histograma colorida (HSI)                           | ⬜     |
| Ajuste de matiz, saturação e brilho                                | ⬜     |
| Ajuste de canal (C/R, M/G, Y/B)                                    | ⬜     |
| Sépia                                                              | ⬜     |
| Demais processamentos funcionando em imagens coloridas             | ⬜     |

> **Nota:** hoje o `load_image` do backend converte toda imagem para escala de cinza (matriz 2D). Para as etapas coloridas, ele precisa passar a devolver `(H, W, 3)`.

## Roadmap

1. ✅ Entrada e saída de imagens
2. ✅ Limiarização
3. ✅ Demais operações pontuais (negativo, brilho, gama, linear por partes)
4. ⬜ Histograma e equalização
5. ⬜ Convolução genérica e filtros espaciais
6. ⬜ Escala e rotação com interpolação
7. ✅ Esteganografia
8. ⬜ Fourier e edição do espectro
9. ⬜ Imagens coloridas (HSI, chroma-key, sépia etc.)
10. 🚧 Interface gráfica integrando tudo (base pronta; cada algoritmo novo ganha um painel)

## Primeiros passos

### Pré-requisitos

- Python 3.10 ou superior
- Um navegador moderno (Chrome, Firefox ou Edge)

### Instalação

```bash
git clone <url-do-repositorio>
cd catpixel

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements/requirements.txt
```

As dependências são `numpy`, `Pillow` (só para abrir e salvar arquivos), `FastAPI`, `uvicorn` e `python-multipart`. Para rodar os testes, use `requirements/requirements-dev.txt`.

## Uso

Inicie o servidor a partir da raiz do projeto:

```bash
uvicorn backend.app:app --reload --port 8765
```

Abra <http://localhost:8765> no navegador. O mesmo servidor entrega a interface e a API (a documentação automática da API fica em `/docs`).

Na interface:

1. Clique em **Abrir imagem** ou arraste um arquivo para a janela.
2. Abra um ajuste no painel da direita (por exemplo, **Limiarização**) e mexa no controle. A pré-visualização aparece na hora.
3. Clique em **Aplicar** para gravar a edição no histórico, ou em **Cancelar**.
4. Use **Ver original** para comparar, o painel **Histórico** (ou Ctrl+Z / Ctrl+Shift+Z) para voltar ou refazer, e o menu **Arquivo** para salvar em BMP ou JPG.
5. Roda do mouse dá zoom e arrastar move a imagem. Duplo clique ajusta à tela.

O servidor guarda uma única imagem em edição, pensada para uso local por uma pessoa.

Os algoritmos de `backend/model/` também funcionam sem a interface:

```python
from backend.model.image_io import load_image, save_image
from backend.model.thresholding import threshold_image

imagem = load_image("imagens/GatoHalloween.jpg")   # matriz 2D uint8 (H, W)
binaria = threshold_image(imagem, 128)             # pixels >= 128 viram 255, os demais 0
save_image(binaria, "saida.bmp")
```

Salve o resultado em BMP. O JPG comprime com perdas e cria tons de cinza nas bordas.

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
│       ├── adjustments-panel.js  # painel de ajustes
│       ├── history-panel.js
│       ├── menubar.js
│       └── toast.js
├── docs/                         # como cada funcionalidade foi feita e como adicionar novas
├── requirements/
├── imagens/                      # imagens de exemplo
└── assets/                       # logos
```

### Como adicionar um novo algoritmo

O passo a passo completo está em [docs/novas-funcionalidades.md](docs/novas-funcionalidades.md), e a explicação de cada funcionalidade (o quê, por quê e como) em [docs/implementacoes.md](docs/implementacoes.md). Resumo:

1. Escreva a função em `backend/model/` e o teste em `backend/tests/`.
2. Registre a operação em `backend/operations.py`.
3. Adicione uma entrada em `ADJUSTMENTS`, em `frontend/js/adjustments-panel.js`, com os controles dela.

## Regras do projeto

- O Pillow é usado **somente** para abrir e salvar arquivos.
- Nenhuma biblioteca de processamento de imagens pode ser usada nos algoritmos. Eles manipulam a matriz da imagem diretamente.
- Bibliotecas de álgebra linear (como o NumPy) são permitidas, mas não suas funções que sejam, elas próprias, requisito do trabalho.
- Se a DFT for implementada de forma ingênua, o programa também deve oferecer uma FFT de biblioteca, para que imagens grandes sejam viáveis.
- Ao exibir o resultado de filtros que geram valores negativos ou acima de 255, normalize os valores apenas para exibição.
