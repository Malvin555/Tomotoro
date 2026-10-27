import { $, $$ } from "./utils/dom.js";

export function initPreviewTabs() {
  const shotTabs = $$('#shotTabs [role="tab"]');
  const panels = $$("[data-panel]");

  if (!shotTabs.length || !panels.length) return;

  const showShot = (name) => {
    panels.forEach((panel) => {
      panel.classList.toggle("hidden", panel.dataset.panel !== name);
    });

    shotTabs.forEach((tab) => {
      const isActive = tab.dataset.shot === name;

      tab.setAttribute("aria-selected", String(isActive));
    });
  };

  shotTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      showShot(tab.dataset.shot);
    });
  });

  showShot("timer");
}
