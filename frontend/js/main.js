import { AdjustmentsPanel } from "./adjustments-panel.js";
import { api } from "./api.js";
import { renderHistory } from "./history-panel.js";
import { buildMenubar } from "./menubar.js";
import { StageView } from "./stage-view.js";
import { showToast } from "./toast.js";

const $ = (id) => document.getElementById(id);

const stage = new StageView();
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

  if (!hasImage) {
    stage.clear();
    $("status-zoom").textContent = "";
    return;
  }
  if (!hasImage || refit) compareSwitch.checked = false;
  stage.setSize(state.width, state.height, { refit });
  showCurrentImage();
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
]);

$("welcome-open").addEventListener("click", chooseFile);
$("tool-zoom-in").addEventListener("click", () => stage.zoomBy(1.5));
$("tool-zoom-out").addEventListener("click", () => stage.zoomBy(1 / 1.5));
$("tool-fit").addEventListener("click", () => stage.fit());
$("tool-actual").addEventListener("click", () => stage.actualSize());
compareSwitch.addEventListener("change", showCurrentImage);
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
