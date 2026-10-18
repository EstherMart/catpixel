/**
 * Barra superior. Cada entrada é de um destes tipos:
 * - menu com lista de itens: { label, items: [{ label, shortcut, action, enabled }] };
 * - botão simples: { key, label, action }, que chama `action` ao ser clicado.
 * Devolve { setActive(key) }, que destaca o botão simples com essa chave.
 */

export function buildMenubar(container, menus) {
  let openMenu = null;

  function close() {
    openMenu?.classList.remove("open");
    openMenu?.querySelector(".menu-list").setAttribute("hidden", "");
    openMenu = null;
  }

  function open(menu, refreshItems) {
    close();
    refreshItems();
    menu.classList.add("open");
    menu.querySelector(".menu-list").removeAttribute("hidden");
    openMenu = menu;
  }

  const plainButtons = new Map(); // botões simples, por chave

  for (const definition of menus) {
    if (!definition.items) {
      const button = document.createElement("button");
      button.className = "menu-trigger";
      button.textContent = definition.label;
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        close();
        definition.action();
      });
      button.addEventListener("pointerenter", () => openMenu && close());
      plainButtons.set(definition.key, button);
      container.append(button);
      continue;
    }

    const menu = document.createElement("div");
    menu.className = "menu";

    const trigger = document.createElement("button");
    trigger.className = "menu-trigger";
    trigger.textContent = definition.label;

    const list = document.createElement("div");
    list.className = "menu-list";
    list.hidden = true;

    const buttons = definition.items.map((item) => {
      if (item === "separator") {
        list.append(Object.assign(document.createElement("div"), { className: "menu-separator" }));
        return null;
      }
      const button = document.createElement("button");
      button.className = "menu-item";
      button.innerHTML = `<span>${item.label}</span><span class="menu-shortcut">${item.shortcut ?? ""}</span>`;
      button.addEventListener("click", () => {
        close();
        item.action();
      });
      list.append(button);
      return { button, item };
    });

    const refreshItems = () => {
      for (const entry of buttons) {
        if (entry) entry.button.disabled = !(entry.item.enabled?.() ?? true);
      }
    };

    trigger.addEventListener("click", (event) => {
      event.stopPropagation();
      menu === openMenu ? close() : open(menu, refreshItems);
    });
    trigger.addEventListener("pointerenter", () => {
      if (openMenu && openMenu !== menu) open(menu, refreshItems);
    });

    menu.append(trigger, list);
    container.append(menu);
  }

  document.addEventListener("click", close);
  document.addEventListener("keydown", (event) => event.key === "Escape" && close());

  return {
    setActive(key) {
      for (const [buttonKey, button] of plainButtons) button.classList.toggle("active", buttonKey === key);
    },
  };
}
