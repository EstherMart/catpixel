/**
 * Controles dos cartões de ajuste. Cada construtor recebe a definição (um item de `controls` em
 * ADJUSTMENTS), coloca os elementos em `body` e devolve { read(), reset() }:
 *   read()  → objeto com os parâmetros que esse controle envia ao backend;
 *   reset() → volta ao valor inicial.
 * `onInput` é chamado a cada mudança, para atualizar a prévia.
 */

const uid = (key) => `adjust-${key}-${Math.random().toString(36).slice(2, 7)}`;

const el = (tag, props = {}) => Object.assign(document.createElement(tag), props);

function labelFor(input, text, className = "") {
  return el("label", { htmlFor: input.id, textContent: text, className });
}

function buildRange(control, body, onInput) {
  const row = el("div", { className: "adjust-row" });
  const input = el("input", { type: "range", min: control.min, max: control.max, step: control.step, value: control.value });
  const value = el("span", { className: "adjust-value", textContent: control.value });
  input.id = uid(control.key);

  input.addEventListener("input", () => {
    value.textContent = input.value;
    onInput();
  });

  row.append(labelFor(input, control.label), input, value);
  body.append(row);

  return {
    read: () => ({ [control.key]: Number(input.value) }),
    reset() {
      input.value = control.value;
      value.textContent = control.value;
    },
  };
}

function buildText(control, body, onInput) {
  const input = el("textarea", { className: "adjust-text", rows: 3, value: control.value });
  input.id = uid(control.key);
  input.addEventListener("input", onInput);
  body.append(labelFor(input, control.label, "adjust-text-label"), input);

  return {
    read: () => ({ [control.key]: input.value }),
    reset: () => (input.value = control.value),
  };
}

/** Lista de opções. O valor enviado é o `value` da opção escolhida (número). */
function buildChoice(control, body, onInput) {
  const row = el("div", { className: "adjust-row" });
  const select = el("select", { className: "adjust-select" });
  control.options.forEach((option) => select.append(el("option", { value: option.value, textContent: option.label })));
  select.value = control.value;
  select.id = uid(control.key);
  select.addEventListener("change", onInput);

  row.append(labelFor(select, control.label), select);
  body.append(row);

  return {
    read: () => ({ [control.key]: Number(select.value) }),
    reset: () => (select.value = control.value),
  };
}

// ---------- filtro por convolução ----------

const KERNEL_SIZES = [3, 5, 7, 9, 11];

const binomial = (size) => {
  let row = [1];
  for (let i = 1; i < size; i++) row = row.map((value, index) => value + (row[index - 1] ?? 0)).concat(1);
  return row;
};

/** Modelos prontos. `fixed` é a dimensão obrigatória; sem ela, o modelo vale para qualquer tamanho. */
const PRESETS = {
  mean: {
    label: "Média",
    build: (n) => ({ cells: Array.from({ length: n }, () => Array(n).fill(1)), divisor: n * n }),
  },
  gaussian: {
    label: "Gaussiana",
    build(n) {
      const row = binomial(n);
      const sum = row.reduce((a, b) => a + b, 0);
      return { cells: row.map((a) => row.map((b) => a * b)), divisor: sum * sum };
    },
  },
  identity: {
    label: "Identidade",
    build: (n) => ({
      cells: Array.from({ length: n }, (_, y) => Array.from({ length: n }, (_, x) => (x === y && x === (n - 1) / 2 ? 1 : 0))),
      divisor: 1,
    }),
  },
  sharpen: {
    label: "Realce de nitidez (3x3)",
    fixed: 3,
    build: () => ({ cells: [[0, -1, 0], [-1, 5, -1], [0, -1, 0]], divisor: 1 }),
  },
  edges: {
    label: "Bordas, Laplaciano (3x3)",
    fixed: 3,
    build: () => ({ cells: [[0, -1, 0], [-1, 4, -1], [0, -1, 0]], divisor: 1 }),
  },
};

/** Grade editável de valores do filtro, com escolha do tamanho, modelos prontos e divisor. */
function buildKernel(control, body, onInput) {
  const sizeSelect = el("select", { className: "adjust-select" });
  KERNEL_SIZES.forEach((n) => sizeSelect.append(el("option", { value: n, textContent: `${n} × ${n}` })));
  sizeSelect.id = uid("size");

  const presetSelect = el("select", { className: "adjust-select" });
  presetSelect.append(el("option", { value: "custom", textContent: "Personalizado" }));
  Object.entries(PRESETS).forEach(([key, preset]) => presetSelect.append(el("option", { value: key, textContent: preset.label })));
  presetSelect.id = uid("preset");

  const grid = el("div", { className: "kernel-grid" });
  const divisorInput = el("input", { type: "number", className: "kernel-divisor", step: "any" });
  divisorInput.id = uid("divisor");

  const sizeRow = el("div", { className: "adjust-row" });
  sizeRow.append(labelFor(sizeSelect, "Tamanho"), sizeSelect);
  const presetRow = el("div", { className: "adjust-row" });
  presetRow.append(labelFor(presetSelect, "Modelo"), presetSelect);
  const divisorRow = el("div", { className: "adjust-row" });
  divisorRow.append(labelFor(divisorInput, "Divisor"), divisorInput);
  body.append(sizeRow, presetRow, grid, divisorRow);

  const cellValues = () => [...grid.children].map((input) => Number(input.value));
  const size = () => Number(sizeSelect.value);

  function fill({ cells, divisor }) {
    const n = cells.length;
    sizeSelect.value = n;
    grid.style.setProperty("--n", n);
    grid.replaceChildren(
      ...cells.flat().map((value) => {
        const input = el("input", { type: "number", className: "kernel-cell", step: "any", value });
        input.addEventListener("input", () => {
          presetSelect.value = "custom";
          onInput();
        });
        return input;
      }),
    );
    divisorInput.value = divisor;
  }

  function applyPreset(key, n) {
    const preset = PRESETS[key];
    fill(preset.build(preset.fixed ?? n));
  }

  /** Muda a dimensão mantendo o centro do filtro atual (ou refazendo o modelo escolhido). */
  function resize(n) {
    const key = presetSelect.value;
    const preset = PRESETS[key];
    if (preset && (preset.fixed ?? n) === n) return applyPreset(key, n);
    presetSelect.value = "custom"; // um modelo de tamanho fixo vira personalizado ao mudar a dimensão

    const old = size();
    const values = cellValues();
    const offset = (n - old) / 2;
    const cells = Array.from({ length: n }, (_, y) =>
      Array.from({ length: n }, (_, x) => {
        const oy = y - offset, ox = x - offset;
        return oy >= 0 && oy < old && ox >= 0 && ox < old ? values[oy * old + ox] : 0;
      }),
    );
    fill({ cells, divisor: Number(divisorInput.value) || 1 });
  }

  sizeSelect.addEventListener("change", () => {
    resize(Number(sizeSelect.value));
    onInput();
  });
  presetSelect.addEventListener("change", () => {
    if (presetSelect.value !== "custom") applyPreset(presetSelect.value, size());
    onInput();
  });
  divisorInput.addEventListener("input", () => {
    presetSelect.value = "custom";
    onInput();
  });

  const reset = () => {
    presetSelect.value = control.preset;
    applyPreset(control.preset, control.size);
  };
  reset();

  return {
    read() {
      const n = size();
      const values = cellValues();
      const kernel = Array.from({ length: n }, (_, y) => values.slice(y * n, (y + 1) * n));
      return { [control.key]: kernel, [control.divisorKey]: Number(divisorInput.value) || 0 };
    },
    reset,
  };
}

const BUILDERS = { range: buildRange, text: buildText, choice: buildChoice, kernel: buildKernel };

export function buildControl(control, body, onInput) {
  return BUILDERS[control.type ?? "range"](control, body, onInput);
}
