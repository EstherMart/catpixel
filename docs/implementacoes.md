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

Esconder é uma operação comum (`"hide_message"`, com o parâmetro de texto `text`), então entra no histórico e pode ser desfeita. O rótulo do histórico não mostra o texto secreto. Revelar devolve texto, não imagem, e por isso tem endpoint próprio: `GET /api/steganography` responde `{"found": bool, "text": str}` e lê a imagem inteira, nunca a prévia reduzida. O botão **Esteganografia**, na barra superior, mostra a operação **Esconder e revelar mensagem**, que abre um painel com um campo de texto, o botão **Esconder** e o botão **Revelar mensagem da imagem**. Não há prévia, porque ela é reduzida e perderia a mensagem.

**Limitações.** Só o BMP guarda a mensagem: o JPG comprime com perdas e apaga os LSBs. Qualquer operação feita depois de esconder (brilho, negativo etc.) também destrói a mensagem, então esconda por último e salve em BMP. Imagens coloridas viram cinza ao abrir (veja [Abrir e salvar imagens](#abrir-e-salvar-imagens)), o que não afeta um BMP cinza salvo por este programa.

## Histograma e convolução

### Exibição do histograma

**O quê.** Mostra, num gráfico de barras, quantos pixels existem em cada intensidade, de 0 (preto) a 255 (branco). O gráfico fica no topo do painel lateral, com a caixa **Escala log.** no título, e se atualiza a cada edição, desfazer ou salto no histórico. Com **Ver original** ligado, mostra o histograma da imagem original.

**Por quê.** O histograma explica o efeito das outras operações: o brilho desloca as barras, o contraste as espalha e a equalização as distribui. Mostrá-lo o tempo todo permite comparar antes e depois sem abrir nada.

**Como.** `compute_histogram(matrix)`, em `backend/model/histogram.py`, percorre cada pixel e soma 1 na posição da intensidade, devolvendo 256 contagens. O endpoint `GET /api/histogram?which=current|original` devolve `{"counts": [...]}`. No frontend, `frontend/js/histogram-panel.js` desenha as barras num `canvas`, com a altura proporcional ao maior valor (cada barra tem pelo menos 2 px, para aparecer em imagens com poucos tons). A caixa **Escala logarítmica** troca a altura por `ln(1 + contagem)`, o que deixa visíveis tons raros ao lado de tons muito frequentes, como o branco numa imagem quase toda preta. `main.js` chama `refreshHistogram()` sempre que a tela é redesenhada. O histograma é da imagem gravada no servidor: durante a pré-visualização de um ajuste ele ainda mostra a imagem atual, e só muda depois de **Aplicar**.

### Equalização de histograma

**O quê.** Redistribui as intensidades para que o histograma fique o mais uniforme possível, o que aumenta o contraste de imagens com poucos tons. A regra é `s = round((cdf(r) − cdf_min) / (N − cdf_min) · 255)`, em que `cdf` é a soma acumulada do histograma, `cdf_min` é o primeiro valor não nulo dela e `N` é o número de pixels.

**Por quê.** Subtrair `cdf_min` faz o menor tom da imagem virar 0 e o maior virar 255, aproveitando todo o intervalo. Uma imagem de um único tom não tem o que equalizar e volta igual, o que também evita divisão por zero.

**Como.** `build_equalization_lut(counts)` e `equalize_histogram(matrix)`, em `backend/model/histogram.py`, calculam a tabela a partir do histograma e a aplicam com `apply_lut`, como nas outras operações pontuais. A operação `"equalize"` não tem parâmetros, e a operação **Equalização de histograma**, na lista do botão **Ajustes**, abre os parâmetros dela. Para ver o efeito, aplique e compare o gráfico do histograma com **Ver original**.

### Filtro genérico por convolução

**O quê.** Cada pixel vira a soma dos seus vizinhos multiplicados pelos valores de um filtro quadrado de dimensão ímpar (3x3, 5x5, 7x7, 9x9 ou 11x11), dividida por um divisor. A imagem de saída tem o mesmo tamanho da original. A pessoa escolhe o tamanho, edita os valores da grade ou parte de um modelo pronto (média, gaussiana, identidade, realce de nitidez e bordas pelo Laplaciano).

**Por quê.** Quase todos os filtros espaciais do trabalho (média, gaussiana, Laplaciano, high-boost, Sobel) são casos particulares dessa operação, então ela é a base para os próximos itens. Os valores do filtro são inteiros e há um campo de divisor, em vez de frações, para que a grade continue legível em filtros grandes: a média 9x9 é "81 vezes o valor 1, dividido por 81".

**Como.** `convolve(matrix, kernel, divisor, normalize)`, em `backend/model/convolution.py`:

1. valida que o filtro é quadrado, de dimensão ímpar (até 15) e só tem números finitos, e que o divisor é finito e diferente de zero (senão `ValueError`);
2. aumenta a imagem de `tamanho // 2` pixels em cada lado, repetindo o pixel mais próximo da borda, para que a saída tenha o tamanho original;
3. para cada posição do filtro, soma na saída a imagem deslocada multiplicada pelo peso. O filtro é girado 180°, como na convolução de verdade (em filtros simétricos isso não muda nada);
4. divide pelo divisor e arredonda;
5. coloca o resultado em 0 a 255.

O passo 3 faz a conta de todos os pixels de uma vez para cada posição do filtro, em vez de um laço pixel a pixel. Isso mantém o resultado idêntico e deixa o filtro 9x9 de uma imagem de 960x540 em menos de 0,1 s. Não é usada nenhuma função pronta de convolução.

O resultado de um filtro pode sair de 0 a 255 (o Laplaciano gera valores negativos, por exemplo). A opção **Resultado** do cartão escolhe o que fazer: **Cortar em 0 a 255** limita os valores, e **Normalizar** leva o menor valor para 0 e o maior para 255, que é o que se quer ver em filtros de borda. Em ambos os casos a imagem gravada no histórico já está em 0 a 255, e o valor real não é guardado.

Ligação com a interface: a operação `"convolution"` recebe `kernel` (lista de listas), `divisor` e `normalize` (0 ou 1). A operação **Filtro por convolução**, na lista do botão **Filtros**, abre o painel de parâmetros, que usa os controles novos de `frontend/js/controls.js` (`kernel` e `choice`). A pré-visualização roda numa versão reduzida da imagem, então o efeito dela parece um pouco mais forte que o resultado final.

## Filtros espaciais

Os filtros desta seção seguem o Capítulo 3 do livro-texto (seções 3.5 e 3.6), estão na lista do botão **Filtros** e usam filtros quadrados de dimensão ímpar, de 3×3 até 11×11. A imagem de saída sempre tem o tamanho da original, e nas bordas o pixel mais próximo é repetido para fora da imagem. O código fica em `backend/model/spatial_filters.py` e reaproveita `convolve_raw`, de `backend/model/convolution.py`.

Sobre os valores fora de 0 a 255: um filtro de derivada (como o Laplaciano) gera valores negativos e maiores que 255. Quando o objetivo é só mostrar o resultado do filtro, os valores são normalizados (o menor vira 0 e o maior vira 255) e a imagem fica acinzentada, porque o zero passa a ser um cinza médio. Isso é feito apenas na opção **Só o laplaciano**. Nos resultados de suavização e de aguçamento, que são imagens comuns, os valores são só limitados a 0 e 255. Todo o cálculo é feito com números reais, e o arredondamento para 8 bits é o último passo.

### Suavização pela média (simples)

**O quê.** Cada pixel vira a média simples dos pixels da vizinhança `n × n`, ele incluído. Isso equivale a um filtro com todos os pesos iguais a 1 e divisor `n²`.

**Por quê.** É o filtro de suavização mais simples e reduz ruído e detalhes finos. Quanto maior a vizinhança, maior o borrão. Uma região de intensidade constante não muda.

**Como.** `mean_filter(matrix, size)` monta o filtro com `mean_kernel(size)` e o aplica com `convolve_raw`. Um tamanho par, menor que 1 ou maior que 15 lança `ValueError`. A operação `"mean"` recebe o inteiro `size`, e a operação **Suavização pela média**, na lista do botão **Filtros**, oferece os tamanhos de 3 a 11 numa lista.

### Suavização Gaussiana (média ponderada)

**O quê.** É uma média ponderada: os pixels perto do centro da vizinhança pesam mais que os das bordas, seguindo o formato de uma gaussiana.

**Por quê.** Com o mesmo tamanho, borra menos os detalhes que a média simples e evita o aspecto "em blocos" do borrão. Os pesos são inteiros (binomiais) e há um divisor, para que a conta continue exata e o filtro possa ser mostrado como grade.

**Como.** `gaussian_kernel(size)` calcula uma linha do triângulo de Pascal (1 2 1 para 3, 1 4 6 4 1 para 5) e faz o produto externo dela consigo mesma. O divisor é a soma de todos os pesos (16 para 3×3 e 256 para 5×5). Os coeficientes binomiais aproximam bem a curva gaussiana. `gaussian_filter(matrix, size)` aplica esse filtro com `convolve_raw`. A operação `"gaussian"` recebe `size`.

### Filtro da mediana

**O quê.** Cada pixel vira a mediana das intensidades da vizinhança `n × n`, ele incluído: ordenam-se os `n²` valores e fica o do meio.

**Por quê.** É um filtro de estatística de ordem, não linear. Elimina pontos isolados (ruído "sal e pimenta") sem borrar as bordas, o que a média não consegue: um pixel muito claro no meio de um fundo escuro faz a média subir, mas não muda a mediana.

**Como.** `median_filter(matrix, size)` não é uma convolução, então não usa filtro. Para cada posição da vizinhança, ela pega a imagem deslocada, empilha todas as camadas, ordena a pilha e escolhe a camada do meio. O trabalho é feito em faixas de 64 linhas, para a pilha não ocupar muita memória em imagens grandes. A operação `"median"` recebe `size`. Numa imagem de 1920×1080, o filtro 9×9 leva cerca de 1 s.

### Aguçamento por Laplaciano

**O quê.** O Laplaciano é a segunda derivada da imagem e realça as mudanças bruscas de intensidade. Há duas máscaras, com centro negativo (Figura 3.37 do livro): a de 4 vizinhos (`0 1 0 / 1 −4 1 / 0 1 0`) e a de 8 vizinhos, com as diagonais (`1 1 1 / 1 −8 1 / 1 1 1`). O aguçamento soma o resultado à imagem original: `g = f + c·∇²f`, com `c = −1` para máscaras de centro negativo, ou seja, `g = f − ∇²f`.

**Por quê.** O Laplaciano sozinho mostra só bordas sobre um fundo escuro. Somá-lo à imagem original devolve as variações gerais de intensidade e aumenta o contraste nas bordas, o que deixa a imagem mais nítida. A máscara de 8 vizinhos realça também as bordas diagonais, e o resultado é mais nítido.

**Como.** `laplacian_filter(matrix, diagonals, sharpen)`, em `backend/model/spatial_filters.py`, calcula o Laplaciano com `convolve_raw`. Com `sharpen=True` (padrão), devolve `f − ∇²f` limitado a 0 e 255. Com `sharpen=False`, devolve só a imagem laplaciana, normalizada para exibição (menor valor em 0 e maior em 255), e por isso ela aparece acinzentada. Uma região de intensidade constante vira cinza médio nesse modo e fica igual no modo de aguçamento. A operação `"laplacian"` recebe `diagonals` e `sharpen` (0 ou 1), escolhidos em duas listas do painel.

### Aguçamento High-Boost

**O quê.** Subtrai da imagem uma versão suavizada dela, o que dá a "máscara de nitidez", e soma essa máscara de volta com um peso `k`: `g = f + k·(f − f_suavizada)`. Com `k = 1` é a máscara de nitidez (unsharp masking), com `k > 1` é o high-boost, e com `k` entre 0 e 1 o realce diminui. Com `k = 0` a imagem não muda.

**Por quê.** A diferença entre a imagem e a versão borrada guarda os detalhes finos e as bordas. O peso `k` controla a intensidade do realce sem trocar de filtro. Limitar o resultado a 0 e 255 evita que o realce produza valores inválidos.

**Como.** `high_boost_filter(matrix, size, k, gaussian)` borra a imagem com a média (`gaussian=False`) ou com a gaussiana (`gaussian=True`) do tamanho `size`, calcula a máscara com números reais e soma `k` vezes ela à original. Um `k` negativo lança `ValueError`. A operação `"highboost"` recebe `size`, `k` (slider de 0 a 5, padrão 2) e `gaussian`.

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

As três operações desta seção estão no botão **Geometria**, usam `backend/model/geometry.py` e seguem a seção 2.4.4 do livro-texto (interpolação de imagens). Todas funcionam por **mapeamento inverso**: para cada pixel da imagem de saída, o programa calcula de onde ele veio na imagem original (uma posição com casas decimais) e estima a intensidade ali por interpolação. O caminho contrário, empurrar cada pixel da entrada para a saída, deixaria buracos na imagem ampliada ou girada. As coordenadas são medidas no centro dos pixels, e o cálculo é feito para todos os pixels de uma vez com numpy, sem biblioteca de imagens.

As duas interpolações são as mesmas na escala e nas rotações:

1. **Vizinho mais próximo.** O pixel de saída copia o pixel original mais próximo da posição calculada. É rápido e não cria tons novos, mas deixa a imagem ampliada em blocos e as bordas girados serrilhadas.
2. **Bilinear.** O pixel de saída é a média ponderada dos 4 pixels vizinhos da posição: `v = (1−dx)(1−dy)·f00 + dx(1−dy)·f10 + (1−dx)dy·f01 + dx·dy·f11`, em que `dx` e `dy` são as distâncias ao pixel de cima e da esquerda. Gera transições suaves, ao custo de um pouco mais de tempo.

### Escala (vizinho mais próximo e bilinear)

**O quê.** Amplia ou reduz a imagem. A largura é multiplicada por `scale_x` e a altura por `scale_y`, e os dois fatores são independentes (de 0,1 a 4 na interface). O resultado tem o tamanho novo: `round(largura · scale_x)` por `round(altura · scale_y)`.

**Por quê.** Fatores separados permitem esticar a imagem em um eixo só. O mapeamento usa o centro dos pixels (`x_origem = (x_saída + 0,5) / escala − 0,5`), assim a imagem não "anda" para um lado ao ampliar e os quatro cantos ficam alinhados. Uma posição calculada fora da imagem repete a borda.

**Como.** `scale_image(matrix, scale_x, scale_y, method)` calcula as coordenadas de origem de cada pixel de saída e as entrega à função de interpolação. `scaled_shape` calcula o tamanho final sem montar a imagem. Fatores menores ou iguais a zero, não numéricos ou que gerem uma imagem de menos de 1 pixel ou de mais de 40 milhões de pixels lançam `ValueError`. A operação `"scale"` recebe `scale_x`, `scale_y` e `method` (0 = vizinho mais próximo, 1 = bilinear). Como a escala muda o tamanho, o histórico mostra o tamanho novo, e a tela reenquadra a imagem. Ampliar 2× uma imagem Full HD leva cerca de 1 s no vizinho mais próximo e 3 s no bilinear.

### Rotação (vizinho mais próximo e bilinear)

**O quê.** Gira a imagem em torno do centro. O ângulo é em graus, positivo no sentido anti-horário e negativo no horário. O que fica fora da imagem original vira preto. A opção **Tela** escolhe entre **Aumentar**, que cria uma imagem maior onde cabe a imagem toda, e **Manter o tamanho**, que corta o que sair.

**Por quê.** O sentido anti-horário é o da trigonometria, o que facilita conferir os testes: 90° dá o mesmo resultado que `numpy.rot90`. Na tela aumentada, o novo tamanho vem dos cantos girados: `largura' = |l·cos θ| + |a·sen θ|` e `altura' = |l·sen θ| + |a·cos θ|`, arredondados para cima.

**Como.** `rotate_image(matrix, angle, method, pivot, expand)` gira cada posição de saída de volta ao ângulo oposto, em torno do pivô: `x_origem = cx + dx·cos θ − dy·sen θ` e `y_origem = cy + dx·sen θ + dy·cos θ`, em que `(dx, dy)` é a distância ao centro da saída (com o eixo y apontando para baixo). Sem `pivot`, o centro da imagem é o pivô. Um ponto é considerado dentro da imagem se estiver a até meio pixel dela, e fora disso fica preto. `rotated_shape` calcula o tamanho final. A operação `"rotate"` recebe `angle`, `expand` (0 ou 1) e `method`.

### Rotação com pivô

**O quê.** Gira a imagem em torno de um ponto escolhido, que fica parado. A tela mantém o tamanho original, então o que girar para fora dela é cortado, e o que sobrar vazio fica preto.

**Por quê.** Girar em torno do centro é um caso particular. O pivô vira um ponto fixo da transformação: ele tem a mesma posição na entrada e na saída. Por isso a tela não cresce aqui, porque aumentá-la deslocaria o pivô. O pedido de aumentar a tela junto com um pivô lança `ValueError`.

**Como.** É a mesma função `rotate_image`, chamada com `pivot=(x, y)` em pixels. A interface recebe o pivô em **porcentagem** da imagem (`pivot_x` e `pivot_y`, de 0 a 100, em que 0% é a esquerda e o topo e 100% é a direita e a base), que o backend converte em pixels com `porcentagem / 100 · (tamanho − 1)`. Dessa forma o mesmo valor funciona em imagens de qualquer tamanho. Valores fora de 0 a 100 lançam `ValueError`. A operação `"rotate_pivot"` recebe `angle`, `pivot_x`, `pivot_y` e `method`.

**Prévia com tamanho diferente.** Como a escala e a rotação aumentada mudam o tamanho, a rota `POST /api/preview` devolve o cabeçalho `X-Result-Size` (`LARGURAxALTURA`) com o tamanho final do resultado, mesmo que a prévia seja reduzida. A tela usa esse valor para desenhar a prévia no quadro certo. Cada operação pode declarar o tamanho do resultado em `result_shape`, em `backend/operations.py`; sem isso, o tamanho não muda.

## Domínio da frequência

Tudo desta seção está em `backend/model/frequency.py` e no botão **Frequência** da barra superior. **Nenhuma função de `numpy.fft` é usada no programa:** as duas transformadas são escritas à mão. O `numpy.fft` aparece apenas nos testes, como referência para conferir os resultados (a diferença é da ordem de 1e-10).

### Transformada Discreta de Fourier

**O quê.** Transforma a imagem em uma matriz de números complexos que diz quanto de cada frequência a imagem contém. A DFT 2D de uma imagem `f` de `M × N` pixels é `F(u, v) = Σx Σy f(x, y) · e^(−j·2π·(ux/M + vy/N))`.

**Por quê.** Como a exponencial se separa em uma parte de `x` e outra de `y`, a DFT 2D é uma DFT 1D em cada linha seguida de uma DFT 1D em cada coluna. Escrita como multiplicação de matrizes, fica `F = W_M · f · W_N`, em que `W[k, n] = e^(−j·2π·k·n/N)`. Isso é a definição, sem atalhos, e funciona para qualquer tamanho de imagem. O custo é proporcional ao cubo do lado, então a versão ingênua só aceita imagens de até 1024 pixels de lado (cerca de 1 s no 1024 × 1024) e responde com uma mensagem pedindo a FFT nas maiores.

**Como.** `dft2(matrix)` monta as duas matrizes de Fourier e as multiplica. A inversa, `idft2(spectrum)`, usa as matrizes conjugadas e divide por `M · N`. Na interface, o algoritmo **DFT (ingênua, lenta)** é uma das opções do editor de espectro.

### Transformada Rápida de Fourier (FFT)

**O quê.** O mesmo resultado da DFT, calculado em tempo proporcional a `N·log N` por linha. É a implementação própria do algoritmo de Cooley-Tukey radix-2, que vale pontos extras no enunciado.

**Por quê.** O algoritmo divide a transformada de `N` pontos em duas de `N/2` (pontos de índice par e ímpar) e as junta com `X = par + w·ímpar` e `Y = par − w·ímpar`, em que `w = e^(−j·2π·k/N)` é o fator de rotação. Isso exige que `N` seja potência de 2. Por isso a imagem é completada com zeros, embaixo e à direita, até os dois lados serem potências de 2 (1280 × 720 vira 2048 × 1024), e o resultado é cortado de volta ao tamanho original depois da inversa. Esse preenchimento tem dois efeitos visíveis: aparece uma "cruz" brilhante no espectro (a borda abrupta entre a imagem e os zeros) e a frequência zero guarda a média **contando os zeros**, então um filtro que só deixa a frequência zero produz uma imagem lisa mais escura que a média original.

**Como.** `fft2(matrix)` e `ifft2(spectrum)`. A função `_fft_last_axis` reordena os elementos pela inversão dos bits do índice e depois junta blocos de tamanho 1, 2, 4, 8 e assim por diante. Cada etapa faz as contas de todas as linhas ao mesmo tempo com numpy, e a transformada 2D é a das linhas seguida da das colunas. Uma imagem 1280 × 720 (2048 × 1024 depois do preenchimento) leva cerca de 1,4 s. O lado máximo depois do preenchimento é 2048, e imagens maiores recebem uma mensagem sugerindo reduzir com a escala. A inversa usa o sinal oposto no expoente e divide por `M · N`.

### Espectro deslocado com edição pelo usuário

**O quê.** O botão **Frequência → Espectro de Fourier** mostra, na área da imagem, o espectro com a frequência zero no centro, e a pessoa pinta nele com o mouse. O pincel pode ser **preto** (elimina as frequências pintadas), **branco** (mantém ou restaura) ou **cinza** (atenua pelo tom escolhido), com tamanho de 2 a 200 pixels e **maciez** de 0 (borda dura) a 100 (pincel suave, que vai ficando transparente da ponta para a borda).

**Por quê.** Na saída da DFT a frequência zero fica no canto. Deslocar o espectro (`shift`, que gira a matriz de `altura/2` e `largura/2`) a leva para o centro, e então as frequências baixas (formas grandes) ficam perto do centro e as altas (detalhes e bordas) longe dele. A magnitude é mostrada em escala logarítmica, `s = 255 · ln(1 + |F|) / ln(1 + |F|máx)`, porque a frequência zero é milhares de vezes maior que as outras e, sem o logaritmo, só o ponto central apareceria. A pessoa não edita os números: ela pinta uma **máscara** em tons de cinza do tamanho do espectro (preto = 0, branco = 1). O espectro de uma imagem real é simétrico em torno do centro, então a caixa **Espelhar no lado oposto** (ligada por padrão) repete cada pincelada no ponto simétrico, e a imagem filtrada continua real.

**Como.** O endpoint `GET /api/spectrum?algorithm=0|1` calcula o espectro da imagem atual (0 = FFT e 1 = DFT) e devolve a imagem em PNG, com o tamanho em `X-Spectrum-Size` e o tempo em `X-Seconds`. No frontend, o controle `spectrum`, em `frontend/js/controls.js`, mostra essa imagem na área central e coloca um `canvas` por cima, no mesmo tamanho do espectro e com mistura multiplicativa (branco não muda nada, preto escurece). O pincel carimba círculos ao longo do traço, e o zoom da tela continua funcionando. O botão do meio do mouse move a imagem, já que o botão esquerdo está pintando. **Limpar edições** volta a máscara ao branco. Enquanto o editor está aberto não há pré-visualização, porque a tela está ocupada com o espectro: o resultado só aparece em **Aplicar filtro**, e pode ser desfeito no histórico.

### Transformada inversa

**O quê.** Aplica a transformada inversa ao espectro multiplicado pela máscara e obtém a imagem filtrada: `f' = IDFT(F · M)`. Máscara toda branca devolve a imagem original, preta zera tudo, e um círculo preto no centro deixa só os detalhes (passa-alta).

**Por quê.** Multiplicar o espectro pela máscara é a definição de um filtro no domínio da frequência. A conta é sempre feita sobre o espectro original da imagem atual, por isso a operação não guarda estado no servidor e entra no histórico como qualquer outra. O resultado da inversa é complexo, e só a parte real é usada. Ela pode sair de 0 a 255 (um passa-alta remove a frequência zero e gera valores negativos), e a opção **Resultado** escolhe entre **Cortar em 0 a 255** e **Normalizar**, que leva o menor valor a 0 e o maior a 255, e a imagem fica acinzentada, como na convolução.

**Como.** `filter_with_mask(matrix, mask, algorithm, normalize)`: calcula o espectro, redimensiona a máscara com a interpolação bilinear se o tamanho for outro (o que também faz a pré-visualização reduzida funcionar), multiplica, desfaz o deslocamento (`unshift`), aplica a inversa, corta o preenchimento e converte para 8 bits. A operação `"frequency_filter"` recebe `mask` (a máscara em PNG codificada em base64), `algorithm` (0 ou 1) e `normalize` (0 ou 1). Uma máscara que não seja uma imagem válida lança `ValueError`.

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
