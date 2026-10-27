import { initTheme } from "./theme.js";
import { initPomodoro } from "./pomodoro.js";
import { initPreviewTabs } from "./preview-tabs.js";
import { initClipboard } from "./clipboard.js";

function initApp() {
  initTheme();
  initPomodoro();
  initPreviewTabs();
  initClipboard();
}

document.addEventListener("DOMContentLoaded", initApp);

document.addEventListener("astro:page-load", initApp);
