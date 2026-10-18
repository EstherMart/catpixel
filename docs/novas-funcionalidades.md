# Como adicionar uma nova funcionalidade

Exemplo usado nos passos: o **negativo**. O modelo é a limiarização, que já está pronta.

Cada funcionalidade passa por duas partes: o **backend** faz a conta, e o **frontend** mostra os controles. A API (`/api/preview` e `/api/apply`) é genérica e **não precisa mudar** para operações que recebem a imagem e números e devolvem uma imagem.

## 1. Backend (Python)

1. **Escreva o algoritmo** em `backend/model/<nome>.py`, por exemplo `point_operations.py`.
   - Receba a matriz numpy (`np.ndarray`) e devolva uma matriz nova, sem alterar a de entrada.
   - Valide os parâmetros e lance `ValueError` com mensagem clara quando forem inválidos.
   - Não importe nada de web (FastAPI, requests) aqui. Pillow só em `image_io.py`.
   - Não use funções de biblioteca que sejam o próprio requisito do trabalho. Manipule a matriz diretamente.
   - O repositório tem um limite de **25 testes** no total (hoje são 25, então o limite foi atingido). Cada teste cobre uma funcionalidade e reúne várias verificações. Para uma funcionalidade nova, acrescente verificações a um teste existente do mesmo assunto em `backend/tests/` (ou junte testes antigos) em vez de criar um teste novo, e evite `parametrize`, que conta um teste por caso. Confira com `python -m pytest --collect-only -q`.
2. **Registre a operação** em `backend/operations.py`, no dicionário `OPERATIONS`:

   ```python
   "negative": Operation(
       label=lambda params: "Negativo",
       run=lambda matrix, params: negative_image(matrix),
   ),
   ```

   - `label` é o texto que aparece no histórico.
   - `run` recebe a matriz e os parâmetros (`params`) vindos do navegador. Valide o tipo de cada parâmetro (veja `_int_param`). Para parâmetros decimais, use `_number_param`, que aceita `int` e `float` (o navegador pode mandar `1` no lugar de `1.0`). Para texto, use `_text_param`. Todo erro de parâmetro deve ser `ValueError`: a API só trata esse tipo (e `KeyError`), e qualquer outro vira erro 500.

## 2. Frontend (JavaScript)

Em `frontend/js/adjustments-panel.js`, adicione uma entrada em `ADJUSTMENTS`. O campo `group` escolhe em qual botão da barra superior a operação aparece. As chaves e os nomes estão em `GROUPS`; para uma categoria nova, acrescente uma linha lá e ela ganha um botão. Clicar no botão mostra a lista das operações dele no painel lateral, e escolher uma operação mostra os parâmetros dela:

```js
{
  op: "negative",                 // igual à chave registrada em OPERATIONS
  group: "tones",                 // botão "Ajustes" da barra superior
  title: "Negativo",
  hint: "Inverte as intensidades: cada pixel vira 255 menos o valor original.",
  controls: [],                   // sem parâmetros: o cartão só tem Aplicar e Cancelar
},
```

Para uma operação com parâmetros, cada item de `controls` vira um slider:

```js
controls: [{ key: "limit", label: "Limiar", min: 0, max: 255, step: 1, value: 128 }]
```

Sem `type`, o controle é um slider. Os outros tipos, definidos em `frontend/js/controls.js`, são `text` (caixa de texto), `choice` (lista de opções com `options: [{ label, value }]`), `kernel` (grade do filtro de convolução), `spectrum` (editor do espectro), `color` (seletor de cor, que envia `<prefix>_r`, `<prefix>_g` e `<prefix>_b`) e `image-file` (escolha de um arquivo de imagem, enviado em base64). Para criar um tipo novo, escreva uma função que devolva `{ read(), reset() }` e registre-a em `BUILDERS`. Um controle que precise preparar algo quando o cartão abre (como carregar uma imagem) pode devolver também `open()`. Os controles recebem um quarto argumento, `context`, com `api`, `showError`, o elemento `wrap` da imagem e as funções `showSpectrum(url, largura, altura)` e `restoreImage()`, para trocar a imagem exibida na área central; o `reset()` do controle deve chamar `restoreImage()`. Use `preview: false` na entrada de `ADJUSTMENTS` quando a área central estiver ocupada pelo controle.

- `key` é o nome do parâmetro no backend (em `params`).
- `value` é o valor inicial.
- A pré-visualização, o botão **Aplicar**, o histórico e o desfazer funcionam sozinhos.

## 3. Documentação

1. Descreva a funcionalidade em [implementacoes.md](implementacoes.md), respondendo **o quê**, **por quê** e **como**.
2. Marque ✅ na tabela de funcionalidades do [README](../README.md).

## 4. Conferir

```bash
uvicorn backend.app:app --reload --port 8765
```

Abra `http://localhost:8765`, abra uma imagem e experimente a nova operação na lista do botão dela. Rode também `python -m pytest`.

## Quando é preciso mais que isso

O caminho acima serve para operações que mudam a imagem a partir de números. Alguns itens do trabalho pedem algo a mais:

| Funcionalidade | O que muda |
| --- | --- |
| Histograma (já feito, serve de modelo) | Não devolve imagem. Tem o endpoint `GET /api/histogram`, que devolve as contagens, e o painel `frontend/js/histogram-panel.js`, que desenha o gráfico. |
| Filtro por convolução (já feito, serve de modelo) | Usa o controle `kernel` (tamanho, modelos prontos, grade de valores e divisor) e o controle `choice` (lista de opções). O backend recebe a matriz do filtro em `params`. Os filtros espaciais prontos (média, gaussiana, mediana, Laplaciano e high-boost) estão em `backend/model/spatial_filters.py`, e novos filtros lineares (como o Sobel) podem reaproveitar `convolve_raw`, de `backend/model/convolution.py`, que devolve os valores reais, sem limitar a 0 a 255. |
| Chroma-key | Precisa enviar uma segunda imagem (a que substitui o fundo). Crie um endpoint de upload e um controle de arquivo. |
| Espectro de Fourier editável (já feito, serve de modelo) | O editor é o controle `spectrum`, em `frontend/js/controls.js`: mostra uma imagem na área central e pinta uma máscara num `canvas` por cima. A operação `"frequency_filter"` recebe a máscara como PNG em base64 em `params` e não guarda estado no servidor. O endpoint `GET /api/spectrum` devolve a imagem do espectro. Veja também o parágrafo sobre controles que mexem na tela, acima. |
| Operação que muda o tamanho da imagem (escala e rotação, já feitas) | Declare `result_shape` na `Operation`, em `backend/operations.py`, com a função que calcula (altura, largura) do resultado. A rota de prévia envia esse tamanho no cabeçalho `X-Result-Size`, e a tela desenha a prévia reduzida no quadro certo. |
| Esteganografia (já feita, serve de modelo) | Esconder é uma operação comum. Ler devolve texto, então tem o endpoint próprio `GET /api/steganography`. No frontend, use um controle com `type: "text"` e `reveal: true` em `ADJUSTMENTS`, e `preview: false` quando a prévia reduzida não faz sentido. |
| Imagens coloridas (já feitas) | Uma imagem colorida é uma matriz `(altura, largura, 3)`. Uma operação nova de cinza **já funciona em cores sozinha**: `run_operation` a roda em cada canal. Se ela precisar ver os três canais juntos (conversões de cor, equalização, esteganografia), marque `native=True` na `Operation` e trate imagens 2D e 3D. Operações só de cor devem aceitar cinza com `as_color`, de `backend/model/color.py`, em vez de dar erro, para a pré-visualização não gerar avisos. Para pedir um arquivo de imagem (como o fundo do chroma-key), use o controle `image-file`, e para uma cor, o controle `color`. |
| Resultados fora de 0 a 255 (filtros, Sobel) | Normalize os valores só para exibir, como o enunciado pede. Guarde o resultado real no histórico. |
