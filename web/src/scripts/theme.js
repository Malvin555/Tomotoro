import { $ } from "./utils/dom.js";

export function initTheme() {
  const root = document.documentElement;
  const themeToggle = $("#themeToggle");

  if (!themeToggle) return;

  // Restore saved theme
  try {
    const saved = localStorage.getItem("theme");

    if (saved === "light" || saved === "dark") {
      root.dataset.theme = saved;
    }
  } catch {}

  themeToggle.addEventListener("click", () => {
    const current = getComputedStyle(root).colorScheme;

    const next = current === "dark" ? "light" : "dark";

    root.dataset.theme = next;

    try {
      localStorage.setItem("theme", next);
    } catch {}
  });
}
