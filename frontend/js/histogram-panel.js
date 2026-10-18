/**
 * Gráfico do histograma: uma barra por intensidade, de 0 (preto) a 255 (branco).
 * Em imagem em cinza é um histograma só. Em imagem colorida são quatro: R, G, B e I (intensidade).
 * A escala logarítmica deixa visíveis os tons raros ao lado de tons muito frequentes.
 */

const MIN_BAR_PX = 2;
const CHANNEL_COLORS = { r: "255, 90, 90", g: "70, 220, 110", b: "90, 140, 255" };

export class HistogramPanel {
  #container;
  #canvas;
  #legend;
  #data = null;
  #logScale = false;

  /** `logCheckbox` é a caixa de escala logarítmica, que fica no título do painel. */
  constructor(container, logCheckbox) {
    this.#container = container;
    this.#canvas = Object.assign(document.createElement("canvas"), { className: "histogram-canvas" });
    this.#legend = Object.assign(document.createElement("div"), { className: "histogram-legend" });
    logCheckbox.addEventListener("change", () => {
      this.#logScale = logCheckbox.checked;
      if (this.#data) this.draw(this.#data);
    });
    window.addEventListener("resize", () => this.#data && this.draw(this.#data));
    this.clear();
  }

  clear() {
    this.#data = null;
    const note = Object.assign(document.createElement("p"), {
      className: "histogram-note", textContent: "O histograma aparece ao abrir uma imagem.",
    });
    this.#container.replaceChildren(note);
  }

  /** data: { counts, channels } — `counts` é a intensidade e `channels` ({ r, g, b }) só existe em imagem colorida. */
  draw(data) {
    this.#data = data;
    if (!this.#canvas.isConnected) {
      const axis = Object.assign(document.createElement("div"), { className: "histogram-axis" });
      axis.append(...["0", "128", "255"].map((text) => Object.assign(document.createElement("span"), { textContent: text })));
      this.#container.replaceChildren(this.#canvas, axis, this.#legend);
    }
    this.#renderLegend(Boolean(data.channels));

    const ratio = window.devicePixelRatio || 1;
    const { width, height } = this.#canvas.getBoundingClientRect();
    this.#canvas.width = Math.round(width * ratio);
    this.#canvas.height = Math.round(height * ratio);

    const context = this.#canvas.getContext("2d");
    context.clearRect(0, 0, this.#canvas.width, this.#canvas.height);

    const scale = this.#logScale ? Math.log1p : (count) => count;
    const series = data.channels
      ? [...Object.entries(data.channels).map(([name, counts]) => ({ counts, fill: `rgba(${CHANNEL_COLORS[name]}, 0.55)` })), { counts: data.counts, line: "rgba(255, 255, 255, 0.9)" }]
      : [{ counts: data.counts, fill: getComputedStyle(document.documentElement).getPropertyValue("--green").trim() }];
    const peak = Math.max(...series.flatMap(({ counts }) => counts.map(scale)), 1);

    context.globalCompositeOperation = data.channels ? "lighter" : "source-over"; // R + G + B sobrepostos clareiam
    for (const { counts, fill, line } of series) {
      if (fill) this.#drawBars(context, counts, scale, peak, fill);
      else this.#drawLine(context, counts, scale, peak, line, ratio);
    }
  }

  #drawBars(context, counts, scale, peak, fill) {
    const slot = this.#canvas.width / counts.length;
    const barWidth = Math.max(slot, MIN_BAR_PX * (window.devicePixelRatio || 1));
    context.fillStyle = fill;
    counts.forEach((count, level) => {
      const barHeight = (scale(count) / peak) * (this.#canvas.height - 4);
      // a barra é centrada na sua posição, para que 0 e 255 não saiam do gráfico
      const x = Math.min(Math.max(level * slot + slot / 2 - barWidth / 2, 0), this.#canvas.width - barWidth);
      context.fillRect(x, this.#canvas.height - barHeight, barWidth, barHeight);
    });
  }

  #drawLine(context, counts, scale, peak, color, ratio) {
    const slot = this.#canvas.width / counts.length;
    context.strokeStyle = color;
    context.lineWidth = ratio;
    context.beginPath();
    counts.forEach((count, level) => {
      const x = level * slot + slot / 2;
      const y = this.#canvas.height - (scale(count) / peak) * (this.#canvas.height - 4);
      level === 0 ? context.moveTo(x, y) : context.lineTo(x, y);
    });
    context.stroke();
  }

  #renderLegend(isColor) {
    this.#legend.hidden = !isColor;
    if (!isColor || this.#legend.childElementCount) return;
    for (const [name, color] of [["R", CHANNEL_COLORS.r], ["G", CHANNEL_COLORS.g], ["B", CHANNEL_COLORS.b], ["I", "255, 255, 255"]]) {
      this.#legend.append(Object.assign(document.createElement("span"), { textContent: name, style: `color: rgb(${color})` }));
    }
  }
}
