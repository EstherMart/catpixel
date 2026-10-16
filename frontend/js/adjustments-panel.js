/**
 * Painel de ajustes. Cada ajuste é uma entrada em ADJUSTMENTS ligada a uma operação do backend.
 * Para ter um novo ajuste: registrar a operação em backend/operations.py e listar aqui.
 */

const ADJUSTMENTS = [
  {
    op: "threshold",
    title: "Limiarização",
    hint: "Pixels com intensidade a partir do limiar ficam brancos; os demais, pretos.",
    controls: [{ key: "limit", label: "Limiar", min: 0, max: 255, step: 1, value: 128 }],
  },

  {
    op: "negative",
    title: "Negativo",
    hint: "Inverte as intensidades da imagem.",
    controls: [],
  },

  {
    op: "brightness",
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
    title: "Logaritmo",
    hint: "Expande os níveis escuros e comprime os claros.",
    controls: [],
  },

  {
    op: "piecewise",
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
    op: "hide_message",
    title: "Esteganografia",
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
  #previewTimer;

  /** callbacks: { preview(op, params), apply(op, params), cancel(), reveal() → texto ou null } */
  constructor(container, callbacks) {
    this.#container = container;
    this.#callbacks = callbacks;
    ADJUSTMENTS.forEach((adjustment) => this.#cards.push(this.#buildCard(adjustment)));

    const note = document.createElement("p");
    note.className = "coming-soon";
    note.textContent = "Novos ajustes e filtros chegam aqui a cada aula.";
    container.append(note);
  }

  setEnabled(enabled) {
    this.#container.classList.toggle("disabled", !enabled);
    if (!enabled) this.#closeActive();
  }

  /** Chamado quando o histórico muda por fora (desfazer, voltar passo): descarta a prévia aberta. */
  resetControls() {
    this.#closeActive();
  }

  #buildCard(adjustment) {
    const card = document.createElement("section");
    card.className = "adjust-card";

    const header = document.createElement("button");
    header.className = "adjust-header";
    header.textContent = adjustment.title;

    const body = document.createElement("div");
    body.className = "adjust-body";
    body.hidden = true;

    const hint = document.createElement("p");
    hint.className = "adjust-hint";
    hint.textContent = adjustment.hint;
    body.append(hint);

    const inputs = adjustment.controls.map((control) => this.#buildControl(control, body, () => this.#schedulePreview()));

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
    header.addEventListener("click", () => (this.#active === entry ? this.#closeActive(true) : this.#open(entry)));
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

  #buildControl(control, body, onInput) {
    if (control.type === "text") return this.#buildTextControl(control, body, onInput);
    const row = document.createElement("div");
    row.className = "adjust-row";

    const label = Object.assign(document.createElement("label"), { textContent: control.label });
    const input = Object.assign(document.createElement("input"), {
      type: "range", min: control.min, max: control.max, step: control.step, value: control.value,
    });
    const value = Object.assign(document.createElement("span"), {
      className: "adjust-value", textContent: control.value,
    });
    input.id = `adjust-${control.key}-${Math.random().toString(36).slice(2, 7)}`;
    label.htmlFor = input.id;

    input.addEventListener("input", () => {
      value.textContent = input.value;
      onInput();
    });

    row.append(label, input, value);
    body.append(row);
    return { control, input, value };
  }

  #buildTextControl(control, body, onInput) {
    const label = Object.assign(document.createElement("label"), { className: "adjust-text-label", textContent: control.label });
    const input = Object.assign(document.createElement("textarea"), {
      className: "adjust-text", rows: 3, value: control.value,
    });
    input.id = `adjust-${control.key}-${Math.random().toString(36).slice(2, 7)}`;
    label.htmlFor = input.id;
    input.addEventListener("input", onInput);
    body.append(label, input);
    return { control, input, value: null };
  }

  #paramsOf(entry) {
    return Object.fromEntries(
      entry.inputs.map(({ control, input }) => [
        control.key,
        control.type === "text" ? input.value : Number(input.value),
      ]),
    );
  }

  #open(entry) {
    this.#closeActive(true);
    this.#active = entry;
    entry.card.classList.add("open");
    entry.body.hidden = false;
    this.#schedulePreview();
  }

  #closeActive(cancelPreview = false) {
    clearTimeout(this.#previewTimer);
    const entry = this.#active;
    if (!entry) return;
    this.#active = null;
    entry.card.classList.remove("open");
    entry.body.hidden = true;
    for (const { control, input, value } of entry.inputs) {
      input.value = control.value;
      if (value) value.textContent = control.value;
    }
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
