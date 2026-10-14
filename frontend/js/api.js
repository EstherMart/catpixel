/** Chamadas ao backend. Toda função devolve o estado da edição ou lança Error com a mensagem da API. */

async function readError(response) {
  const body = await response.json().catch(() => ({}));
  const detail = Array.isArray(body.detail) ? "Parâmetros inválidos." : body.detail;
  return new Error(detail || `Erro ${response.status} ao falar com o servidor.`);
}

async function request(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw await readError(response);
  return response;
}

function postJson(url, body = {}, signal) {
  return request(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
}

export const api = {
  async getState() {
    return (await request("/api/state")).json();
  },

  async open(file) {
    const form = new FormData();
    form.append("file", file);
    return (await request("/api/open", { method: "POST", body: form })).json();
  },

  async apply(op, params) {
    return (await postJson("/api/apply", { op, params })).json();
  },

  /** Devolve uma versão reduzida da imagem com a operação aplicada, sem gravar no histórico. */
  async preview(op, params, signal) {
    return (await postJson("/api/preview", { op, params }, signal)).blob();
  },

  async undo() { return (await postJson("/api/undo")).json(); },
  async redo() { return (await postJson("/api/redo")).json(); },
  async reset() { return (await postJson("/api/reset")).json(); },
  async jump(index) { return (await postJson(`/api/jump/${index}`)).json(); },

  imageUrl: (version, which = "current") => `/api/image?which=${which}&v=${version}`,
  saveUrl: (format) => `/api/save?format=${format}`,
};
