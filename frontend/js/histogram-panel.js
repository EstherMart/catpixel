/**
 * Gráfico do histograma: uma barra por intensidade, de 0 (preto) a 255 (branco).
 * A escala logarítmica deixa visíveis os tons raros ao lado de tons muito frequentes.
 */

const MIN_BAR_PX = 2;

export class HistogramPanel {
  #container;
  #canvas;
  #counts = null;
  #logScale = false;

  /** `logCheckbox` é a caixa de escala logarítmica, que fica no título do painel. */
  constructor(container, logCheckbox) {
    this.#container = container;
    this.#canvas = Object.assign(document.createElement("canvas"), { className: "histogram-canvas" });
    logCheckbox.addEventListener("change", () => {
      this.#logScale = logCheckbox.checked;
      if (this.#counts) this.draw(this.#counts);
    });
    window.addEventListener("resize", () => this.#counts && this.draw(this.#counts));
    this.clear();
  }

  clear() {
    this.#counts = null;
    const note = Object.assign(document.createElement("p"), {
      className: "histogram-note", textContent: "O histograma aparece ao abrir uma imagem.",
    });
    this.#container.replaceChildren(note);
  }

  draw(counts) {
    this.#counts = counts;
    if (!this.#canvas.isConnected) {
      const axis = Object.assign(document.createElement("div"), { className: "histogram-axis" });
      axis.append(...["0", "128", "255"].map((text) => Object.assign(document.createElement("span"), { textContent: text })));
      this.#container.replaceChildren(this.#canvas, axis);
    }

    const ratio = window.devicePixelRatio || 1;
    const { width, height } = this.#canvas.getBoundingClientRect();
    this.#canvas.width = Math.round(width * ratio);
    this.#canvas.height = Math.round(height * ratio);

    const context = this.#canvas.getContext("2d");
    context.clearRect(0, 0, this.#canvas.width, this.#canvas.height);
    context.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--green").trim();

    const scale = this.#logScale ? Math.log1p : (count) => count;
    const peak = Math.max(...counts.map(scale), 1);
    const slot = this.#canvas.width / counts.length;
    const barWidth = Math.max(slot, MIN_BAR_PX * ratio);
    counts.forEach((count, level) => {
      const barHeight = (scale(count) / peak) * (this.#canvas.height - 4);
      // a barra é centrada na sua posição, para que 0 e 255 não saiam do gráfico
      const x = Math.min(Math.max(level * slot + slot / 2 - barWidth / 2, 0), this.#canvas.width - barWidth);
      context.fillRect(x, this.#canvas.height - barHeight, barWidth, barHeight);
    });
  }
}
