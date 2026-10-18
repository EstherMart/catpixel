/** Área central: exibe a imagem com zoom (roda do mouse) e movimento (arrastar). */

const MIN_SCALE = 0.05;
const MAX_SCALE = 64;
const MAX_FIT_SCALE = 8;
const FIT_MARGIN = 64;
const ZOOM_STEP = 1.15;
const PIXELATED_FROM_SCALE = 2;

export class StageView {
  #stage = document.getElementById("stage");
  #wrap = document.getElementById("canvas-wrap");
  #img = document.getElementById("doc");
  #size = { width: 0, height: 0 };
  #scale = 1;
  #pan = { x: 0, y: 0 };
  #fitMode = true;
  #drag = null;

  onZoomChange = () => {};

  constructor() {
    this.#stage.addEventListener("wheel", (event) => this.#onWheel(event), { passive: false });
    this.#stage.addEventListener("pointerdown", (event) => this.#startDrag(event));
    this.#stage.addEventListener("pointermove", (event) => this.#moveDrag(event));
    this.#stage.addEventListener("pointerup", () => this.#endDrag());
    this.#stage.addEventListener("pointercancel", () => this.#endDrag());
    this.#stage.addEventListener("dblclick", () => this.fit());
    new ResizeObserver(() => this.#fitMode && this.fit()).observe(this.#stage);
  }

  get hasImage() {
    return this.#size.width > 0;
  }

  /** Define o tamanho real da imagem (a exibida pode ser uma prévia reduzida). */
  setSize(width, height, { refit }) {
    this.#size = { width, height };
    this.#img.style.width = `${width}px`;
    this.#img.style.height = `${height}px`;
    this.#wrap.hidden = false;
    this.#stage.classList.remove("empty");
    if (refit) this.fit();
    else this.#apply();
  }

  showUrl(url) {
    this.#img.src = url;
  }

  clear() {
    this.#size = { width: 0, height: 0 };
    this.#wrap.hidden = true;
    this.#img.removeAttribute("src");
    this.#stage.classList.add("empty");
  }

  fit() {
    if (!this.hasImage) return;
    const availableWidth = Math.max(this.#stage.clientWidth - FIT_MARGIN, 1);
    const availableHeight = Math.max(this.#stage.clientHeight - FIT_MARGIN, 1);
    const scale = Math.min(availableWidth / this.#size.width, availableHeight / this.#size.height);
    this.#fitMode = true;
    this.#pan = { x: 0, y: 0 };
    this.#setScale(Math.min(scale, MAX_FIT_SCALE));
  }

  actualSize() {
    this.#fitMode = false;
    this.#pan = { x: 0, y: 0 };
    this.#setScale(1);
  }

  zoomBy(factor) {
    this.#zoomAround(0, 0, this.#scale * factor);
  }

  #zoomAround(centerX, centerY, newScale) {
    if (!this.hasImage) return;
    const scale = Math.min(Math.max(newScale, MIN_SCALE), MAX_SCALE);
    const imageX = (centerX - this.#pan.x) / this.#scale;
    const imageY = (centerY - this.#pan.y) / this.#scale;
    this.#pan = { x: centerX - imageX * scale, y: centerY - imageY * scale };
    this.#fitMode = false;
    this.#setScale(scale);
  }

  #setScale(scale) {
    this.#scale = scale;
    this.#apply();
    this.onZoomChange(scale);
  }

  #apply() {
    const { x, y } = this.#pan;
    this.#wrap.style.transform = `translate(-50%, -50%) translate(${x}px, ${y}px) scale(${this.#scale})`;
    this.#img.classList.toggle("pixelated", this.#scale >= PIXELATED_FROM_SCALE);
  }

  #onWheel(event) {
    event.preventDefault();
    const rect = this.#stage.getBoundingClientRect();
    const centerX = event.clientX - rect.left - rect.width / 2;
    const centerY = event.clientY - rect.top - rect.height / 2;
    this.#zoomAround(centerX, centerY, this.#scale * ZOOM_STEP ** (-event.deltaY / 100));
  }

  #startDrag(event) {
    if (!this.hasImage || (event.button !== 0 && event.button !== 1)) return;
    if (event.button === 1) event.preventDefault(); // evita a rolagem automática do botão do meio
    this.#drag = { x: event.clientX - this.#pan.x, y: event.clientY - this.#pan.y };
    this.#stage.setPointerCapture(event.pointerId);
    this.#stage.classList.add("panning");
  }

  #moveDrag(event) {
    if (!this.#drag) return;
    this.#pan = { x: event.clientX - this.#drag.x, y: event.clientY - this.#drag.y };
    this.#apply();
  }

  #endDrag() {
    this.#drag = null;
    this.#stage.classList.remove("panning");
  }
}
