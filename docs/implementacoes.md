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

**O quê.** Inverte as intensidades: `s = 255 - r`. Preto vira branco e branco vira preto.

**Por quê.** É a operação ponto a ponto mais simples. Aplicar o negativo duas vezes devolve a imagem original, e os testes usam essa propriedade.

**Como.** `negative_image(matrix)`, em `backend/model/negative.py`, valida que a matriz é 2D, percorre cada pixel e grava `255 - intensidade` numa matriz nova. A operação `"negative"` em `backend/operations.py` não tem parâmetros, e o cartão **Negativo** em `ADJUSTMENTS` só tem Aplicar e Cancelar.

### Brilho

**O quê.** Multiplica cada intensidade por um fator `k` e limita o resultado a 0 e 255: `s = clip(r · k, 0, 255)`. Com `k = 1` a imagem não muda, com `k = 0` fica toda preta e com `k > 1` clareia.

**Por quê.** O brilho é multiplicativo: o preto continua preto e os tons altos clareiam mais. A versão aditiva (`s = r + c`) levanta a imagem inteira por igual e "lava" os escuros. Se o professor pedir a aditiva, basta trocar a conta que monta a LUT.

**Como.** `build_brightness_lut(k)`, em `backend/model/brightness.py`, calcula a saída para os 256 tons e arredonda para o inteiro mais próximo. `adjust_brightness` aplica a tabela com `apply_lut` (`backend/model/utils/lut.py`). O fator precisa ser finito e não negativo, senão a função lança `ValueError`. As demais operações pontuais usam a mesma LUT: a função é calculada uma vez para os 256 tons e cada pixel só consulta a tabela. A operação `"brightness"` recebe o parâmetro decimal `factor`, e o slider vai de 0 a 3, com passo 0,1 e padrão 1.

A função `mean_brightness`, no mesmo arquivo, ainda não é usada por nada.

### Potência (correção de gama)

**O quê.** `s = 255 · (r / 255)^γ`, com `γ > 0`. Com `γ < 1` a imagem clareia (realça os tons escuros), com `γ > 1` escurece e com `γ = 1` não muda. Preto e branco ficam fixos.

**Por quê.** Dividir `r` por 255 antes de elevar mantém a saída entre 0 e 255 e fixa os extremos. Sem essa normalização, o valor estouraria.

**Como.** `build_gamma_lut(γ)` e `gamma_correction(matrix, γ)`, em `backend/model/gamma_log.py`. A operação `"gamma"` recebe o parâmetro `gamma`, e o slider vai de 0,1 a 3, com padrão 1.

**Logaritmo (extra).** O mesmo arquivo traz `log_transformation`: `s = c · ln(1 + r)`, com `c = 255 / ln(256)` para que 255 continue em 255. Ela expande os tons escuros e comprime os claros. A operação `"log"` não tem parâmetros.

### Linear definida por partes

**O quê.** Uma função feita de retas que ligam os pontos `(0,0) → (r1,s1) → (r2,s2) → (255,255)`: o tom `r` da entrada vira o tom `s` da saída. É o alongamento de contraste clássico. Aproximar `r1` de `r2` e afastar `s1` de `s2` dá mais contraste ao intervalo do meio.

**Por quê.** Dois pontos de controle cobrem os casos vistos em aula (contraste, limiarização suave, inversão parcial) e cabem em quatro sliders, que uma pessoa leiga consegue usar. O gráfico sempre passa por `(0,0)` e `(255,255)`.

**Como.** `build_piecewise_lut(points)`, em `backend/model/piecewise_linear.py`, interpola linearmente entre os vértices e `piecewise_linear(matrix, r1, s1, r2, s2)` aplica a LUT. Valores fora de 0 a 255 lançam `ValueError`. Pontos fora de ordem (`r1 > r2`) são ordenados em vez de gerar erro, porque o slider passa por essa situação enquanto a pessoa arrasta, e cada erro viraria um aviso na tela. Dois pontos com o mesmo `r` formam um degrau, parecido com a limiarização. Trechos de largura zero são pulados, o que evita divisão por zero. A operação `"piecewise"` recebe `r1`, `s1`, `r2` e `s2`, com quatro sliders de 0 a 255. O padrão (85,85) e (170,170) fica na diagonal e não muda a imagem.

### Esteganografia

**O quê.** Esconde um texto nos pixels sem mudar a aparência da imagem e lê esse texto de volta.

**Por quê.** Trocar o bit menos significativo (LSB) de um pixel muda a intensidade em no máximo 1 tom de 256, e o olho não percebe. Cada pixel guarda 1 bit.

**Como.** `backend/model/steganography.py` tem três funções:

- `hide_message(matrix, text)` grava, pixel a pixel e linha por linha, os bits de: assinatura `"CP"` (2 bytes), tamanho da mensagem (4 bytes) e texto em UTF-8, que preserva acentos. Devolve uma matriz nova.
- `reveal_message(matrix)` lê o cabeçalho e devolve o texto. Se a assinatura não bater, o tamanho for impossível ou o UTF-8 for inválido, devolve `None`. Assim, uma imagem sem mensagem mostra "nenhuma mensagem" e não lixo.
- `capacity_bytes(matrix)` calcula `(largura · altura − 48) // 8`. Uma mensagem maior que isso lança `ValueError`.

Esconder é uma operação comum (`"hide_message"`, com o parâmetro de texto `text`), então entra no histórico e pode ser desfeita. O rótulo do histórico não mostra o texto secreto. Revelar devolve texto, não imagem, e por isso tem endpoint próprio: `GET /api/steganography` responde `{"found": bool, "text": str}` e lê a imagem inteira, nunca a prévia reduzida. O cartão **Esteganografia** tem um campo de texto, o botão **Esconder** e o botão **Revelar mensagem da imagem**. Não há prévia, porque ela é reduzida e perderia a mensagem.

**Limitações.** Só o BMP guarda a mensagem: o JPG comprime com perdas e apaga os LSBs. Qualquer operação feita depois de esconder (brilho, negativo etc.) também destrói a mensagem, então esconda por último e salve em BMP. Imagens coloridas viram cinza ao abrir (veja [Abrir e salvar imagens](#abrir-e-salvar-imagens)), o que não afeta um BMP cinza salvo por este programa.

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
