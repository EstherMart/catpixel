const VISIBLE_MS = 3500;
let timer;

export function showToast(message, { error = false } = {}) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.toggle("error", error);
  toast.classList.add("visible");
  clearTimeout(timer);
  timer = setTimeout(() => toast.classList.remove("visible"), VISIBLE_MS);
}
