/** Lista os passos da edição. Clicar em um passo volta a ele (os seguintes ainda podem ser refeitos). */

export function renderHistory(container, state, onSelect) {
  container.replaceChildren();

  if (!state.has_image) {
    const note = document.createElement("li");
    note.className = "empty-note";
    note.textContent = "As edições aparecem aqui.";
    container.append(note);
    return;
  }

  state.history.forEach((label, index) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.className = "history-item";
    if (index === state.index) button.classList.add("current");
    if (index > state.index) button.classList.add("future");
    button.textContent = label;
    button.addEventListener("click", () => onSelect(index));
    item.append(button);
    container.append(item);
  });

  container.querySelector(".current")?.scrollIntoView({ block: "nearest" });
}
