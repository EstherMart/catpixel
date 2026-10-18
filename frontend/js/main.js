import { AdjustmentsPanel, GROUPS } from "./adjustments-panel.js?v=5";
import { api } from "./api.js?v=5";
import { HistogramPanel } from "./histogram-panel.js?v=5";
import { renderHistory } from "./history-panel.js?v=5";
import { buildMenubar } from "./menubar.js?v=5";
import { StageView } from "./stage-view.js?v=5";
import { showToast } from "./toast.js?v=5";

const $ = (id) => document.getElementById(id);

const stage = new StageView();
const histogram = new HistogramPanel($("histogram"), $("histogram-log"));
const fileInput = $("file-input");
const compareSwitch = $("compare");

let state = { has_image: false };
let previewUrl = null;
let previewRequest = null;

// ---------- estado e tela ----------

function showError(error) {
  if (error.name !== "AbortError") showToast(error.message, { error: true });
}

async function update(action, { refit = false } = {}) {
  try {
    setState(await action(), { refit });
  } catch (error) {
    showError(error);
  }
}

function setState(next, { refit }) {
  discardPreview();
  state = next;
  adjustments.resetControls();
  render(refit);
}

function render(refit = false) {
  const hasImage = state.has_image;

  $("welcome").hidden = hasImage;
  compareSwitch.disabled = !hasImage;
  adjustments.setEnabled(hasImage);
  renderHistory($("history"), state, (index) => update(() => api.jump(index)));
  $("doc-title").textContent = hasImage ? state.name : "";
  $("status-info").textContent = hasImage
    ? `${state.name}  ·  ${state.width} × ${state.height} px`
    : "Nenhuma imagem aberta";

  refreshHistogram();

  if (!hasImage) {
    stage.clear();
    frameSize = "";
    $("status-zoom").textContent = "";
    return;
  }
  if (!hasImage || refit) compareSwitch.checked = false;
  setFrame(state.width, state.height, { refit });
  showCurrentImage();
}

let histogramRequest = 0;

/** Desenha o histograma da imagem que está na tela (a original, se "Ver original" estiver ligado). */
async function refreshHistogram() {
  if (!state.has_image) return histogram.clear();
  const request = ++histogramRequest;
  try {
    const data = await api.histogram(compareSwitch.checked ? "original" : "current");
    if (request === histogramRequest) histogram.draw(data);
  } catch (error) {
    showError(error);
  }
}

let frameSize = "";

/** Ajusta o quadro da imagem na tela e reenquadra o zoom quando o tamanho muda. */
function setFrame(width, height, { refit = false } = {}) {
  const size = `${width}x${height}`;
  stage.setSize(width, height, { refit: refit || size !== frameSize });
  frameSize = size;
}

function showCurrentImage() {
  if (compareSwitch.checked) stage.showUrl(api.imageUrl(state.version, "original"));
  else stage.showUrl(previewUrl ?? api.imageUrl(state.version));
}

// ---------- prévia dos ajustes ----------

function discardPreview() {
  previewRequest?.abort();
  previewRequest = null;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;
}

async function previewAdjustment(op, params) {
  previewRequest?.abort();
  previewRequest = new AbortController();
  try {
    const { blob, width, height } = await api.preview(op, params, previewRequest.signal);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(blob);
    compareSwitch.checked = false;
    setFrame(width, height); // escala e rotação podem mudar o tamanho
    showCurrentImage();
  } catch (error) {
    showError(error);
  }
}

function cancelPreview() {
  discardPreview();
  if (!state.has_image) return;
  setFrame(state.width, state.height);
  showCurrentImage();
}

/** O que controles especiais (como o editor de espectro) podem fazer na área da imagem. */
const stageContext = {
  api,
  showError,
  wrap: $("canvas-wrap"),
  showSpectrum(url, width, height) {
    discardPreview();
    frameSize = `espectro ${width}x${height}`;
    stage.setSize(width, height, { refit: true });
    stage.showUrl(url);
  },
  restoreImage() {
    frameSize = "";
    if (!state.has_image) return;
    setFrame(state.width, state.height, { refit: true });
    showCurrentImage();
  },
};

const adjustments = new AdjustmentsPanel($("adjustments"), {
  context: stageContext,
  preview: previewAdjustment,
  apply: (op, params) => update(() => api.apply(op, params)),
  cancel: cancelPreview,
  reveal: async () => {
    try {
      return await api.revealMessage();
    } catch (error) {
      showError(error);
    }
  },
});

// ---------- arquivos ----------

function chooseFile() {
  fileInput.click();
}

async function openFile(file) {
  if (!file) return;
  await update(() => api.open(file), { refit: true });
  if (state.has_image) showToast(`${file.name} aberta.`);
}

function download(format) {
  if (!state.has_image) return;
  Object.assign(document.createElement("a"), { href: api.saveUrl(format) }).click();
}

fileInput.addEventListener("change", () => {
  openFile(fileInput.files[0]);
  fileInput.value = "";
});

let dragDepth = 0;
const hasFiles = (event) => event.dataTransfer?.types.includes("Files");
window.addEventListener("dragenter", (event) => {
  if (!hasFiles(event)) return;
  dragDepth++;
  $("drop-overlay").hidden = false;
});
window.addEventListener("dragleave", () => {
  dragDepth = Math.max(dragDepth - 1, 0);
  if (dragDepth === 0) $("drop-overlay").hidden = true;
});
window.addEventListener("dragover", (event) => event.preventDefault());
window.addEventListener("drop", (event) => {
  event.preventDefault();
  dragDepth = 0;
  $("drop-overlay").hidden = true;
  openFile(event.dataTransfer.files[0]);
});

// ---------- ações ----------

const undo = () => state.index > 0 && update(api.undo);
const redo = () => state.index < state.history.length - 1 && update(api.redo);
const hasImage = () => state.has_image;

const menubar = buildMenubar($("menus"), [
  {
    label: "Arquivo",
    items: [
      { label: "Abrir…", shortcut: "Ctrl+O", action: chooseFile },
      "separator",
      { label: "Salvar como BMP", shortcut: "Ctrl+S", action: () => download("bmp"), enabled: hasImage },
      { label: "Salvar como JPG", action: () => download("jpg"), enabled: hasImage },
    ],
  },
  // um botão por grupo: mostra a lista das operações dele no painel lateral
  ...Object.entries(GROUPS).map(([key, label]) => ({ key, label, action: () => showGroup(key) })),
]);

$("history-toggle").addEventListener("click", () => {
  const collapsed = $("panel-history").classList.toggle("collapsed");
  $("history-toggle").setAttribute("aria-expanded", String(!collapsed));
});
function showGroup(key) {
  adjustments.showGroup(key);
  menubar.setActive(key);
}
showGroup(Object.keys(GROUPS)[0]);

$("welcome-open").addEventListener("click", chooseFile);
$("tool-zoom-in").addEventListener("click", () => stage.zoomBy(1.5));
$("tool-zoom-out").addEventListener("click", () => stage.zoomBy(1 / 1.5));
$("tool-fit").addEventListener("click", () => stage.fit());
$("tool-actual").addEventListener("click", () => stage.actualSize());
compareSwitch.addEventListener("change", () => {
  showCurrentImage();
  refreshHistogram();
});
stage.onZoomChange = (scale) => ($("status-zoom").textContent = `Zoom ${Math.round(scale * 100)}%`);

document.addEventListener("keydown", (event) => {
  if (!(event.ctrlKey || event.metaKey)) return;
  const key = event.key.toLowerCase();
  const shortcuts = {
    o: chooseFile,
    s: () => download("bmp"),
    z: event.shiftKey ? redo : undo,
    y: redo,
  };
  if (shortcuts[key]) {
    event.preventDefault();
    shortcuts[key]();
  }
});

// Se a página for recarregada, o servidor ainda guarda a imagem em edição.
update(api.getState, { refit: true });
