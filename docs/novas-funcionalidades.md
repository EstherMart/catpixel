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
   - `run` recebe a matriz e os parâmetros (`params`) vindos do navegador. Valide o tipo de cada parâmetro (veja `_int_param`). Para parâmetros decimais, crie um auxiliar parecido que aceite `int` e `float`, porque o navegador pode mandar `1` no lugar de `1.0`.

## 2. Frontend (JavaScript)

Em `frontend/js/adjustments-panel.js`, adicione uma entrada em `ADJUSTMENTS`:

```js
{
  op: "negative",                 // igual à chave registrada em OPERATIONS
  title: "Negativo",
  hint: "Inverte as intensidades: cada pixel vira 255 menos o valor original.",
  controls: [],                   // sem parâmetros: o cartão só tem Aplicar e Cancelar
},
```

Para uma operação com parâmetros, cada item de `controls` vira um slider:

```js
controls: [{ key: "limit", label: "Limiar", min: 0, max: 255, step: 1, value: 128 }]
```

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

Abra `http://localhost:8765`, abra uma imagem e experimente o novo cartão.

## Quando é preciso mais que isso

O caminho acima serve para operações que mudam a imagem a partir de números. Alguns itens do trabalho pedem algo a mais:

| Funcionalidade | O que muda |
| --- | --- |
| Histograma | Não devolve imagem. Crie um endpoint (por exemplo `GET /api/histogram`) que devolva as contagens, e um painel novo no frontend que desenhe o gráfico. |
| Filtro por convolução com tamanho e valores escolhidos | Precisa de um controle novo no frontend (tamanho do filtro e grade de valores). O backend recebe a matriz do filtro em `params`. |
| Chroma-key | Precisa enviar uma segunda imagem (a que substitui o fundo). Crie um endpoint de upload e um controle de arquivo. |
| Espectro de Fourier editável | Precisa de um editor de desenho (pincel) no frontend e de endpoints que guardem o espectro e apliquem a inversa. |
| Esteganografia | Esconder e ler uma mensagem pede entrada de texto e, na leitura, mostrar texto em vez de imagem. |
| Imagens coloridas | Hoje a matriz é 2D (cinza). As operações precisam aceitar matrizes `(altura, largura, 3)`, e `load_image` e `encode_image` precisam manter as cores. |
| Resultados fora de 0 a 255 (filtros, Sobel) | Normalize os valores só para exibir, como o enunciado pede. Guarde o resultado real no histórico. |
