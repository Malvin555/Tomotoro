import { defineConfig, presetWind4 } from "unocss";

const lightTheme = `
  --bg: #f7f2e8;
  --tint: #ece5d6;
  --ink: #1b1a1f;
  --muted: #5d594f;
  --line: #d9d0bd;
  --accent: #d93a2f;
  --cream: #fff8ec;
  --night: #1b1a1f;
  --win: #fafafb;
  --head: #ebebed;
  --wink: #241f31;
  --row: #f0f0f2;

  --tg-canvas: #f4ede4;
  --tg-card: #fffcf7;
  --tg-raised: #e5ebd9;
  --tg-line: #d8dfd2;
  --tg-ink: #1f3a2e;
  --tg-subtle: #68766b;
  --tg-action: #4a7c59;
  --tg-action-pressed: #3c6748;
  --tg-on-action: #fffcf7;
  --tg-accent-ink: #4a7c59;
  --tg-scrim: rgb(23 41 31 / 0.5);
`;

const darkTheme = `
  --bg: #151418;
  --tint: #1f1d23;
  --ink: #f4efe4;
  --muted: #aaa597;
  --line: #34313a;
  --accent: #e8503f;
  --cream: #fff8ec;
  --night: #0d0c0f;
  --win: #242428;
  --head: #303035;
  --wink: #f6f5f4;
  --row: #2e2e33;

  --tg-canvas: #17291f;
  --tg-card: #22392c;
  --tg-raised: #2d4736;
  --tg-line: #405744;
  --tg-ink: #f4ede4;
  --tg-subtle: #b4c3af;
  --tg-action: #a7c79b;
  --tg-action-pressed: #8caa81;
  --tg-on-action: #1f3a2e;
  --tg-accent-ink: #a7c79b;
  --tg-scrim: rgb(23 41 31 / 0.5);
`;

export default defineConfig({
  presets: [
    presetWind4({
      dark: {
        dark: '[data-theme="dark"]',
        light: '[data-theme="light"]',
      },
    }),
  ],

  preflights: [
    {
      layer: "base",
      getCSS: () => `
        :root {
          box-sizing: border-box;
          padding-top: env(safe-area-inset-top, 0px);
          padding-bottom: env(safe-area-inset-bottom, 0px);
          color-scheme: light;
          ${lightTheme}
        }
        @media (prefers-color-scheme: dark) {
          :root:not([data-theme="light"]) {
            color-scheme: dark;
            ${darkTheme}
          }
        }
        :root[data-theme="dark"] {
          color-scheme: dark;
          ${darkTheme}
        }
      `,
    },
  ],

  theme: {
    colors: {
      bg: "var(--bg)",
      tint: "var(--tint)",
      ink: "var(--ink)",
      muted: "var(--muted)",
      line: "var(--line)",
      accent: "var(--accent)",
      cream: "var(--cream)",
      night: "var(--night)",
      win: "var(--win)",
      head: "var(--head)",
      wink: "var(--wink)",
      row: "var(--row)",

      tg: {
        canvas: "var(--tg-canvas)",
        card: "var(--tg-card)",
        raised: "var(--tg-raised)",
        line: "var(--tg-line)",
        ink: "var(--tg-ink)",
        subtle: "var(--tg-subtle)",
        action: "var(--tg-action)",
        "action-pressed": "var(--tg-action-pressed)",
        "on-action": "var(--tg-on-action)",
        "accent-ink": "var(--tg-accent-ink)",
        scrim: "var(--tg-scrim)",
      },
    },
  },
});
