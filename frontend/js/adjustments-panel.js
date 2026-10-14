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
];

const PREVIEW_DELAY_MS = 60;

export class AdjustmentsPanel {
  #container;
  #callbacks;
  #cards = [];
  #active = null;
  #previewTimer;

  /** callbacks: { preview(op, params), apply(op, params), cancel() } */
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
    const apply = Object.assign(document.createElement("button"), { className: "button primary", textContent: "Aplicar" });
    const actions = document.createElement("div");
    actions.className = "adjust-actions";
    actions.append(cancel, apply);
    body.append(actions);

    const entry = { adjustment, card, body, inputs };
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

  #buildControl(control, body, onInput) {
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

  #paramsOf(entry) {
    return Object.fromEntries(entry.inputs.map(({ control, input }) => [control.key, Number(input.value)]));
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
      value.textContent = control.value;
    }
    if (cancelPreview) this.#callbacks.cancel();
  }

  #schedulePreview() {
    clearTimeout(this.#previewTimer);
    this.#previewTimer = setTimeout(() => {
      if (this.#active) this.#callbacks.preview(this.#active.adjustment.op, this.#paramsOf(this.#active));
    }, PREVIEW_DELAY_MS);
  }
}
