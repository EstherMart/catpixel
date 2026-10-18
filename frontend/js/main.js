import { ADJUSTMENTS, AdjustmentsPanel, GROUPS, QUICK_GROUP } from "./adjustments-panel.js?v=5";
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
    $("status-zoom").textContent = "";
    return;
  }
  if (!hasImage || refit) compareSwitch.checked = false;
  stage.setSize(state.width, state.height, { refit });
  showCurrentImage();
}

let histogramRequest = 0;

/** Desenha o histograma da imagem que está na tela (a original, se "Ver original" estiver ligado). */
async function refreshHistogram() {
  if (!state.has_image) return histogram.clear();
  const request = ++histogramRequest;
  try {
    const counts = await api.histogram(compareSwitch.checked ? "original" : "current");
    if (request === histogramRequest) histogram.draw(counts);
  } catch (error) {
    showError(error);
  }
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
    const blob = await api.preview(op, params, previewRequest.signal);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(blob);
    compareSwitch.checked = false;
    showCurrentImage();
  } catch (error) {
    showError(error);
  }
}

function cancelPreview() {
  discardPreview();
  if (state.has_image) showCurrentImage();
}

const adjustments = new AdjustmentsPanel($("adjustments"), {
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

buildMenubar($("menus"), [
  {
    label: "Arquivo",
    items: [
      { label: "Abrir…", shortcut: "Ctrl+O", action: chooseFile },
      "separator",
      { label: "Salvar como BMP", shortcut: "Ctrl+S", action: () => download("bmp"), enabled: hasImage },
      { label: "Salvar como JPG", action: () => download("jpg"), enabled: hasImage },
    ],
  },
  // um menu por grupo de ajustes (o grupo mais usado fica como atalhos no painel); escolher o item mostra os parâmetros
  ...Object.entries(GROUPS).filter(([key]) => key !== QUICK_GROUP).map(([key, label]) => ({
    label,
    items: ADJUSTMENTS.filter((adjustment) => adjustment.group === key).map((adjustment) => ({
      label: `${adjustment.title}…`,
      action: () => adjustments.open(adjustment.op),
      enabled: hasImage,
    })),
  })),
]);

$("history-toggle").addEventListener("click", () => {
  const collapsed = $("panel-history").classList.toggle("collapsed");
  $("history-toggle").setAttribute("aria-expanded", String(!collapsed));
});
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
