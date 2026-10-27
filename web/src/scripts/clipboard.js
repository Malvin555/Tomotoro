import { $ } from "./utils/dom.js";

export function initClipboard() {
  const copyBtn = $("#copyBtn");

  if (!copyBtn) return;

  copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(copyBtn.dataset.copy);

      copyBtn.textContent = "Copied";
    } catch {
      copyBtn.textContent = "Copy failed";
    }

    setTimeout(() => {
      copyBtn.textContent = "Copy command";
    }, 1800);
  });
}
