# Como adicionar uma nova funcionalidade

Exemplo usado nos passos: o **negativo**. O modelo é a limiarização, que já está pronta.

Cada funcionalidade passa por duas partes: o **backend** faz a conta, e o **frontend** mostra os controles. A API (`/api/preview` e `/api/apply`) é genérica e **não precisa mudar** para operações que recebem a imagem e números e devolvem uma imagem.

## 1. Backend (Python)

1. **Escreva o algoritmo** em `backend/model/<nome>.py`, por exemplo `point_operations.py`.
   - Receba a matriz numpy (`np.ndarray`) e devolva uma matriz nova, sem alterar a de entrada.
   - Valide os parâmetros e lance `ValueError` com mensagem clara quando forem inválidos.
   - Não importe nada de web (FastAPI, requests) aqui. Pillow só em `image_io.py`.
   - Não use funções de biblioteca que sejam o próprio requisito do trabalho. Manipule a matriz diretamente.
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

Em `frontend/js/adjustments-panel.js`, adicione uma entrada em `ADJUSTMENTS`. O campo `group` escolhe onde a operação aparece. As chaves e os nomes estão em `GROUPS`; para uma categoria nova, acrescente uma linha lá e ela vira um menu na barra superior. O grupo `QUICK_GROUP` (`"tones"`, os ajustes mais usados) é a exceção: não vira menu, e sim uma lista de atalhos no painel lateral enquanto nada está aberto. Escolher uma operação mostra os parâmetros dela nesse painel:

```js
{
  op: "negative",                 // igual à chave registrada em OPERATIONS
  group: "tones",                 // grupo "Ajustes": aparece como atalho no painel, sem menu
  title: "Negativo",
  hint: "Inverte as intensidades: cada pixel vira 255 menos o valor original.",
  controls: [],                   // sem parâmetros: o cartão só tem Aplicar e Cancelar
},
```

Para uma operação com parâmetros, cada item de `controls` vira um slider:

```js
controls: [{ key: "limit", label: "Limiar", min: 0, max: 255, step: 1, value: 128 }]
```

Sem `type`, o controle é um slider. Os outros tipos, definidos em `frontend/js/controls.js`, são `text` (caixa de texto), `choice` (lista de opções com `options: [{ label, value }]`) e `kernel` (grade do filtro de convolução). Para criar um tipo novo, escreva uma função que devolva `{ read(), reset() }` e registre-a em `BUILDERS`.

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

Abra `http://localhost:8765`, abra uma imagem e experimente o novo item no menu. Rode também `python -m pytest`.

## Quando é preciso mais que isso

O caminho acima serve para operações que mudam a imagem a partir de números. Alguns itens do trabalho pedem algo a mais:

| Funcionalidade | O que muda |
| --- | --- |
| Histograma (já feito, serve de modelo) | Não devolve imagem. Tem o endpoint `GET /api/histogram`, que devolve as contagens, e o painel `frontend/js/histogram-panel.js`, que desenha o gráfico. |
| Filtro por convolução (já feito, serve de modelo) | Usa o controle `kernel` (tamanho, modelos prontos, grade de valores e divisor) e o controle `choice` (lista de opções). O backend recebe a matriz do filtro em `params`. Novos filtros espaciais (média, Laplaciano, Sobel) podem reaproveitar `convolve` em `backend/model/convolution.py`. |
| Chroma-key | Precisa enviar uma segunda imagem (a que substitui o fundo). Crie um endpoint de upload e um controle de arquivo. |
| Espectro de Fourier editável | Precisa de um editor de desenho (pincel) no frontend e de endpoints que guardem o espectro e apliquem a inversa. |
| Esteganografia (já feita, serve de modelo) | Esconder é uma operação comum. Ler devolve texto, então tem o endpoint próprio `GET /api/steganography`. No frontend, use um controle com `type: "text"` e `reveal: true` em `ADJUSTMENTS`, e `preview: false` quando a prévia reduzida não faz sentido. |
| Imagens coloridas | Hoje a matriz é 2D (cinza). As operações precisam aceitar matrizes `(altura, largura, 3)`, e `load_image` e `encode_image` precisam manter as cores. |
| Resultados fora de 0 a 255 (filtros, Sobel) | Normalize os valores só para exibir, como o enunciado pede. Guarde o resultado real no histórico. |
