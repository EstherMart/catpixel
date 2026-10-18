/**
 * Painel de parâmetros. Cada ajuste é uma entrada em ADJUSTMENTS ligada a uma operação do backend.
 * Para ter um novo ajuste: registrar a operação em backend/operations.py e listar aqui.
 * `group` é a chave de GROUPS: cada grupo vira um botão na barra superior. Clicar nele mostra aqui
 * a lista das operações do grupo, e escolher uma delas mostra os parâmetros dela (um por vez).
 */

import { buildControl } from "./controls.js?v=5";

/** Título de cada menu da barra superior. */
export const GROUPS = {
  tones: "Ajustes",
  filters: "Filtros",
  geometry: "Geometria",
  hide: "Esteganografia",
};

/** Escolha do método de interpolação (a conta da escala e da rotação). */
const methodControl = () => ({
  type: "choice", key: "method", label: "Interpolação", value: 1,
  options: [{ label: "Vizinho mais próximo", value: 0 }, { label: "Bilinear", value: 1 }],
});

/** Tamanhos de filtro oferecidos (quadrados e ímpares). */
const sizeControl = () => ({
  type: "choice", key: "size", label: "Tamanho", value: 3,
  options: [3, 5, 7, 9, 11].map((n) => ({ label: `${n} × ${n}`, value: n })),
});

export const ADJUSTMENTS = [
  {
    op: "threshold",
    group: "tones",
    title: "Limiarização",
    hint: "Pixels com intensidade a partir do limiar ficam brancos; os demais, pretos.",
    controls: [{ key: "limit", label: "Limiar", min: 0, max: 255, step: 1, value: 128 }],
  },

  {
    op: "negative",
    group: "tones",
    title: "Negativo",
    hint: "Inverte as intensidades da imagem.",
    controls: [],
  },

  {
    op: "brightness",
    group: "tones",
    title: "Brilho",
    hint: "Multiplica as intensidades por um fator.",
    controls: [
      {
        key: "factor",
        label: "Fator",
        min: 0,
        max: 3,
        step: 0.1,
        value: 1,
      },
    ],
  },

  {
    op: "gamma",
    group: "tones",
    title: "Potência (Gama)",
    hint: "Ajusta as intensidades por uma função de potência.",
    controls: [
      {
        key: "gamma",
        label: "Gama",
        min: 0.1,
        max: 3,
        step: 0.1,
        value: 1,
      },
    ],
  },
  
  {
    op: "log",
    group: "tones",
    title: "Logaritmo",
    hint: "Expande os níveis escuros e comprime os claros.",
    controls: [],
  },

  {
    op: "piecewise",
    group: "tones",
    title: "Linear por partes",
    hint: "Liga (0,0), (r1,s1), (r2,s2) e (255,255) com retas. Cada ponto diz: o tom r vira o tom s.",
    controls: [
      { key: "r1", label: "r1", min: 0, max: 255, step: 1, value: 85 },
      { key: "s1", label: "s1", min: 0, max: 255, step: 1, value: 85 },
      { key: "r2", label: "r2", min: 0, max: 255, step: 1, value: 170 },
      { key: "s2", label: "s2", min: 0, max: 255, step: 1, value: 170 },
    ],
  },

  {
    op: "equalize",
    group: "tones",
    title: "Equalização de histograma",
    hint: "Espalha as intensidades por todo o intervalo, aumentando o contraste. Compare o histograma antes e depois.",
    controls: [],
  },

  {
    op: "convolution",
    group: "filters",
    title: "Filtro por convolução",
    hint: "Cada pixel vira a soma dos vizinhos multiplicados pelos valores da grade, dividida pelo divisor. Escolha um modelo ou edite os valores.",
    controls: [
      { type: "kernel", key: "kernel", divisorKey: "divisor", size: 3, preset: "mean" },
      {
        type: "choice", key: "normalize", label: "Resultado", value: 0,
        options: [
          { label: "Cortar em 0 a 255", value: 0 },
          { label: "Normalizar (mín a máx)", value: 1 },
        ],
      },
    ],
  },

  {
    op: "mean",
    group: "filters",
    title: "Suavização pela média",
    hint: "Cada pixel vira a média simples da vizinhança. Quanto maior o tamanho, maior o borrão.",
    controls: [sizeControl()],
  },

  {
    op: "gaussian",
    group: "filters",
    title: "Suavização gaussiana",
    hint: "Média ponderada: o centro da vizinhança pesa mais. Borra menos os detalhes que a média simples.",
    controls: [sizeControl()],
  },

  {
    op: "median",
    group: "filters",
    title: "Filtro da mediana",
    hint: "Cada pixel vira a mediana da vizinhança. Remove pontos isolados (ruído sal e pimenta) sem borrar as bordas.",
    controls: [sizeControl()],
  },

  {
    op: "laplacian",
    group: "filters",
    title: "Aguçamento por Laplaciano",
    hint: "Realça mudanças bruscas de intensidade. Soma o laplaciano à imagem para deixá-la mais nítida, ou mostra só a imagem laplaciana.",
    controls: [
      {
        type: "choice", key: "diagonals", label: "Máscara", value: 0,
        options: [{ label: "4 vizinhos", value: 0 }, { label: "8 vizinhos (com diagonais)", value: 1 }],
      },
      {
        type: "choice", key: "sharpen", label: "Resultado", value: 1,
        options: [{ label: "Imagem aguçada", value: 1 }, { label: "Só o laplaciano", value: 0 }],
      },
    ],
  },

  {
    op: "highboost",
    group: "filters",
    title: "Aguçamento high-boost",
    hint: "Soma à imagem k vezes a diferença entre ela e a versão suavizada. Com k = 1 é a máscara de nitidez; com k maior que 1, o realce aumenta.",
    controls: [
      sizeControl(),
      {
        type: "choice", key: "gaussian", label: "Suavização", value: 0,
        options: [{ label: "Média", value: 0 }, { label: "Gaussiana", value: 1 }],
      },
      { key: "k", label: "k", min: 0, max: 5, step: 0.1, value: 2 },
    ],
  },

  {
    op: "scale",
    group: "geometry",
    title: "Escala",
    hint: "Amplia ou reduz a imagem. A largura e a altura têm fatores separados (1 = tamanho atual). A interpolação estima os pixels novos.",
    controls: [
      { key: "scale_x", label: "Largura ×", min: 0.1, max: 4, step: 0.1, value: 1 },
      { key: "scale_y", label: "Altura ×", min: 0.1, max: 4, step: 0.1, value: 1 },
      methodControl(),
    ],
  },

  {
    op: "rotate",
    group: "geometry",
    title: "Rotação",
    hint: "Gira a imagem em torno do centro, no sentido anti-horário (use ângulos negativos para o horário). Em \"Tela\", aumentar mostra a imagem inteira e manter o tamanho corta o que sair. Os cantos vazios ficam pretos.",
    controls: [
      { key: "angle", label: "Ângulo (°)", min: -180, max: 180, step: 1, value: 0 },
      {
        type: "choice", key: "expand", label: "Tela", value: 1,
        options: [{ label: "Aumentar", value: 1 }, { label: "Manter o tamanho", value: 0 }],
      },
      methodControl(),
    ],
  },

  {
    op: "rotate_pivot",
    group: "geometry",
    title: "Rotação com pivô",
    hint: "Gira em torno de um ponto à sua escolha, que fica parado. O pivô é dado em porcentagem da imagem: 0% é a esquerda e o topo, 100% é a direita e a base.",
    controls: [
      { key: "angle", label: "Ângulo (°)", min: -180, max: 180, step: 1, value: 0 },
      { key: "pivot_x", label: "Pivô x (%)", min: 0, max: 100, step: 1, value: 50 },
      { key: "pivot_y", label: "Pivô y (%)", min: 0, max: 100, step: 1, value: 50 },
      methodControl(),
    ],
  },

  {
    op: "hide_message",
    group: "hide",
    title: "Esconder e revelar mensagem",
    hint: "Esconde um texto nos pixels, sem mudar a aparência. Salve em BMP: o JPG apaga a mensagem, e qualquer ajuste feito depois também.",
    preview: false, // a prévia é reduzida e perderia a mensagem
    reveal: true,
    applyLabel: "Esconder",
    controls: [{ type: "text", key: "text", label: "Mensagem", value: "" }],
  },
];

const PREVIEW_DELAY_MS = 60;

export class AdjustmentsPanel {
  #container;
  #callbacks;
  #cards = [];
  #active = null;
  #lists = new Map(); // grupo → lista de operações
  #group = Object.keys(GROUPS)[0];
  #previewTimer;

  /** callbacks: { preview(op, params), apply(op, params), cancel(), reveal() → texto ou null } */
  constructor(container, callbacks) {
    this.#container = container;
    this.#callbacks = callbacks;

    for (const key of Object.keys(GROUPS)) {
      const list = this.#buildList(key);
      this.#lists.set(key, list);
      container.append(list);
    }

    ADJUSTMENTS.forEach((adjustment) => this.#cards.push(this.#buildCard(adjustment)));
    this.#showList();
  }

  /** Mostra a lista das operações do grupo `key` (a operação que estava aberta é cancelada). */
  showGroup(key) {
    if (!this.#lists.has(key)) return;
    this.#group = key;
    this.#closeActive(true);
    this.#showList();
  }

  /** Mostra os parâmetros da operação `op` (a que estava aberta é cancelada). */
  open(op) {
    const entry = this.#cards.find((card) => card.adjustment.op === op);
    if (entry) this.#open(entry);
  }

  setEnabled(enabled) {
    this.#container.classList.toggle("disabled", !enabled);
    if (!enabled) this.#closeActive();
  }

  /** Chamado quando o histórico muda por fora (desfazer, voltar passo): descarta a prévia aberta. */
  resetControls() {
    this.#closeActive();
  }

  /** Lista de operações de um grupo: o que o painel mostra com nenhuma operação aberta. */
  #buildList(key) {
    const list = document.createElement("div");
    list.append(Object.assign(document.createElement("h3"), { className: "quick-title", textContent: GROUPS[key] }));

    for (const adjustment of ADJUSTMENTS.filter((item) => item.group === key)) {
      const button = Object.assign(document.createElement("button"), { className: "quick-item", textContent: adjustment.title });
      button.addEventListener("click", () => this.open(adjustment.op));
      list.append(button);
    }
    return list;
  }

  /** Mostra só a lista do grupo atual (ou nenhuma, se há uma operação aberta). */
  #showList() {
    for (const [key, list] of this.#lists) list.hidden = this.#active !== null || key !== this.#group;
  }

  #buildCard(adjustment) {
    const card = document.createElement("section");
    card.className = "adjust-card";
    card.hidden = true;

    const header = document.createElement("h3");
    header.className = "adjust-header";
    header.textContent = adjustment.title;

    const body = document.createElement("div");
    body.className = "adjust-body";

    const hint = document.createElement("p");
    hint.className = "adjust-hint";
    hint.textContent = adjustment.hint;
    body.append(hint);

    const inputs = adjustment.controls.map((control) => buildControl(control, body, () => this.#schedulePreview()));

    const cancel = Object.assign(document.createElement("button"), { className: "button", textContent: "Cancelar" });
    const apply = Object.assign(document.createElement("button"), {
      className: "button primary", textContent: adjustment.applyLabel ?? "Aplicar",
    });
    const actions = document.createElement("div");
    actions.className = "adjust-actions";
    actions.append(cancel, apply);
    body.append(actions);

    const entry = { adjustment, card, body, inputs, result: null };
    if (adjustment.reveal) this.#addReveal(entry);
    cancel.addEventListener("click", () => this.#closeActive(true));
    apply.addEventListener("click", async () => {
      clearTimeout(this.#previewTimer);
      const params = this.#paramsOf(entry);
      this.#closeActive(false);
      await this.#callbacks.apply(adjustment.op, params);
    });

    card.append(header, body);
    this.#container.append(card);
    return entry;
  }

  /** Botão que lê a mensagem escondida na imagem atual e mostra o texto dentro do cartão. */
  #addReveal(entry) {
    const button = Object.assign(document.createElement("button"), {
      className: "button reveal-button", textContent: "Revelar mensagem da imagem",
    });
    entry.result = Object.assign(document.createElement("p"), { className: "reveal-result", hidden: true });
    button.addEventListener("click", async () => {
      const text = await this.#callbacks.reveal();
      if (text === undefined) return; // erro já mostrado
      entry.result.hidden = false;
      entry.result.classList.toggle("empty", text === null);
      entry.result.textContent = text ?? "Nenhuma mensagem escondida nesta imagem.";
    });
    entry.body.append(button, entry.result);
  }

  #paramsOf(entry) {
    return Object.assign({}, ...entry.inputs.map((input) => input.read()));
  }

  #open(entry) {
    this.#closeActive(true);
    this.#active = entry;
    entry.card.hidden = false;
    this.#showList();
    this.#schedulePreview();
  }

  #closeActive(cancelPreview = false) {
    clearTimeout(this.#previewTimer);
    const entry = this.#active;
    if (!entry) return;
    this.#active = null;
    entry.card.hidden = true;
    this.#showList();
    entry.inputs.forEach((input) => input.reset());
    if (entry.result) entry.result.hidden = true;
    if (cancelPreview) this.#callbacks.cancel();
  }

  #schedulePreview() {
    clearTimeout(this.#previewTimer);
    if (this.#active?.adjustment.preview === false) return;
    this.#previewTimer = setTimeout(() => {
      if (this.#active) this.#callbacks.preview(this.#active.adjustment.op, this.#paramsOf(this.#active));
    }, PREVIEW_DELAY_MS);
  }
}
