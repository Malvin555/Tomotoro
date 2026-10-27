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
            height: ${segment.min === 25 ? 100 : segment.min === 15 ? 65 : 45}%;
            padding: 8px clamp(2px, 1vw, 12px);
            box-sizing: border-box;
            border-radius: 12px;
          "
        >
          <span class="hidden whitespace-nowrap font-display text-sm font-extrabold sm:block">
            ${segment.min}
          </span>

          <span class="hidden whitespace-nowrap text-xs opacity-80 lg:block">
            ${segment.label}
          </span>
        </div>
      `,
    )
    .join("");
}
