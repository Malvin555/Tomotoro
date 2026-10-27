import { $ } from "./utils/dom.js";

const cycle = [
  { label: "Focus", min: 25, color: "var(--accent)" },
  { label: "Short break", min: 5, color: "var(--ink)" },
  { label: "Focus", min: 25, color: "var(--accent)" },
  { label: "Short break", min: 5, color: "var(--ink)" },
  { label: "Focus", min: 25, color: "var(--accent)" },
  { label: "Short break", min: 5, color: "var(--ink)" },
  { label: "Focus", min: 25, color: "var(--accent)" },
];

export function initPomodoro() {
  const cycleBar = $("#cycleBar");

  if (!cycleBar) return;

  cycleBar.innerHTML = cycle
    .map(
      (segment) => `
        <div
          class="cycle-seg flex min-w-0 flex-col justify-end overflow-hidden"
          style="
            flex: ${segment.min} 1 0%;
            background: ${segment.color};
            color: ${segment.label === "Short break" ? "var(--tint)" : "var(--ink)"};
            height: ${segment.min === 25 ? 100 : 45}%;
            padding: 16px clamp(4px, 1.5vw, 20px);
            box-sizing: border-box;
            border-radius: 12px;
          "
        >
          <span class="font-display text-sm font-extrabold sm:text-lg">
            ${segment.min}
          </span>

          <span class="hidden text-xs opacity-80 sm:block">
            ${segment.label}
          </span>
        </div>
      `,
    )
    .join("");
}
