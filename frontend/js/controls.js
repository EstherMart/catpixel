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

// ---------- edição do espectro de Fourier ----------

const BRUSH_LEVELS = { black: 0, white: 255 };

/** PNG de 1 pixel branco: máscara "sem edição", usada se o espectro não chegou a ser carregado. */
function whiteMask() {
  const canvas = Object.assign(document.createElement("canvas"), { width: 1, height: 1 });
  const context = canvas.getContext("2d");
  context.fillStyle = "#fff";
  context.fillRect(0, 0, 1, 1);
  return canvas.toDataURL("image/png").split(",")[1];
}

/**
 * Editor do espectro: mostra o espectro na área da imagem e deixa a pessoa pintar uma máscara por cima.
 * Preto zera as frequências, branco as mantém e cinza as atenua; o pincel pode ser duro ou suave.
 * Devolve { mask, algorithm }: a máscara em PNG (base64) e o algoritmo (0 = FFT, 1 = DFT).
 */
function buildSpectrum(control, body, onInput, context) {
  const rangeRow = (label, min, max, value) => {
    const row = el("div", { className: "adjust-row" });
    const input = el("input", { type: "range", min, max, step: 1, value });
    const text = el("span", { className: "adjust-value", textContent: value });
    input.id = uid("spectrum");
    input.addEventListener("input", () => (text.textContent = input.value));
    row.append(labelFor(input, label), input, text);
    body.append(row);
    return input;
  };
  const selectRow = (label, options) => {
    const row = el("div", { className: "adjust-row" });
    const select = el("select", { className: "adjust-select" });
    options.forEach(([value, text]) => select.append(el("option", { value, textContent: text })));
    select.id = uid("spectrum");
    row.append(labelFor(select, label), select);
    body.append(row);
    return select;
  };

  const algorithm = selectRow("Algoritmo", [[0, "FFT (rápida)"], [1, "DFT (ingênua, lenta)"]]);
  const tool = selectRow("Pincel", [["black", "Preto (elimina)"], ["white", "Branco (mantém)"], ["gray", "Cinza (atenua)"]]);
  const size = rangeRow("Tamanho", 2, 200, 30);
  const softness = rangeRow("Maciez", 0, 100, 0);
  const gray = rangeRow("Cinza", 0, 255, 128);

  const mirrorRow = el("label", { className: "spectrum-mirror" });
  const mirror = el("input", { type: "checkbox", checked: true });
  mirrorRow.append(mirror, " Espelhar no lado oposto (mantém a simetria do espectro)");
  const clear = el("button", { className: "button spectrum-clear", textContent: "Limpar edições" });
  const status = el("p", { className: "spectrum-status", textContent: "Abra o editor para carregar o espectro." });
  body.append(mirrorRow, clear, status);

  let canvas = null;
  let url = null;
  let drawing = null; // última posição do pincel enquanto o botão está apertado

  const level = () => (tool.value === "gray" ? Number(gray.value) : BRUSH_LEVELS[tool.value]);

  function fillWhite() {
    const painter = canvas.getContext("2d");
    painter.globalCompositeOperation = "source-over";
    painter.fillStyle = "#fff";
    painter.fillRect(0, 0, canvas.width, canvas.height);
  }

  function stamp(x, y) {
    const painter = canvas.getContext("2d");
    const radius = Number(size.value) / 2;
    const hardness = 1 - Number(softness.value) / 100;
    const tone = level();
    const paint = (alpha) => `rgba(${tone}, ${tone}, ${tone}, ${alpha})`;

    if (hardness >= 0.99) {
      painter.fillStyle = paint(1);
      painter.beginPath();
      painter.arc(x, y, radius, 0, 2 * Math.PI);
      painter.fill();
      return;
    }
    // pincel suave: opaco no miolo e transparente na borda; cada toque soma ao anterior
    const gradient = painter.createRadialGradient(x, y, 0, x, y, radius);
    gradient.addColorStop(0, paint(1));
    gradient.addColorStop(hardness, paint(1));
    gradient.addColorStop(1, paint(0));
    painter.fillStyle = gradient;
    painter.fillRect(x - radius, y - radius, radius * 2, radius * 2);
  }

  function stampBoth(x, y) {
    stamp(x, y);
    if (mirror.checked) {
      // o espectro de uma imagem real é simétrico em torno da frequência zero (o centro); pintar os dois lados
      // mantém isso, e a transformada inversa continua sendo uma imagem real
      stamp(2 * Math.floor(canvas.width / 2) + 1 - x, 2 * Math.floor(canvas.height / 2) + 1 - y);
    }
  }

  function strokeTo(x, y) {
    const spacing = Math.max(1, (Number(size.value) / 2) * 0.25);
    const distance = Math.hypot(x - drawing.x, y - drawing.y);
    const steps = Math.max(1, Math.ceil(distance / spacing));
    for (let step = 1; step <= steps; step++) {
      stampBoth(drawing.x + ((x - drawing.x) * step) / steps, drawing.y + ((y - drawing.y) * step) / steps);
    }
    drawing = { x, y };
  }

  const position = (event) => {
    const rect = canvas.getBoundingClientRect();
    return { x: ((event.clientX - rect.left) * canvas.width) / rect.width, y: ((event.clientY - rect.top) * canvas.height) / rect.height };
  };

  function discard() {
    canvas?.remove();
    canvas = null;
    if (url) URL.revokeObjectURL(url);
    url = null;
  }

  async function load() {
    discard();
    status.textContent = "Calculando o espectro…";
    try {
      const { blob, width, height, seconds } = await context.api.spectrum(Number(algorithm.value));
      url = URL.createObjectURL(blob);
      canvas = el("canvas", { width, height, className: "spectrum-mask" });
      fillWhite();
      canvas.addEventListener("pointerdown", (event) => {
        if (event.button !== 0) return; // os outros botões continuam arrastando a imagem
        event.stopPropagation();
        canvas.setPointerCapture(event.pointerId);
        drawing = position(event);
        stampBoth(drawing.x, drawing.y);
      });
      canvas.addEventListener("pointermove", (event) => drawing && strokeTo(...Object.values(position(event))));
      canvas.addEventListener("pointerup", () => (drawing = null));
      canvas.addEventListener("pointercancel", () => (drawing = null));
      context.wrap.append(canvas);
      context.showSpectrum(url, width, height);
      status.textContent = `Espectro ${width} × ${height} calculado em ${seconds} s. Pinte sobre ele; o botão do meio do mouse move a imagem.`;
    } catch (error) {
      status.textContent = error.message;
      context.showError(error);
    }
  }

  algorithm.addEventListener("change", load);
  clear.addEventListener("click", () => canvas && fillWhite());

  return {
    open: load,
    read: () => ({
      [control.key]: canvas ? canvas.toDataURL("image/png").split(",")[1] : whiteMask(),
      algorithm: Number(algorithm.value),
    }),
    reset() {
      discard();
      algorithm.value = 0;
      status.textContent = "Abra o editor para carregar o espectro.";
      context.restoreImage();
    },
  };
}

const BUILDERS = { range: buildRange, text: buildText, choice: buildChoice, kernel: buildKernel, spectrum: buildSpectrum };

export function buildControl(control, body, onInput, context) {
  return BUILDERS[control.type ?? "range"](control, body, onInput, context);
}
