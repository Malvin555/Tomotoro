import { defineConfig } from "astro/config";
import { fileURLToPath } from "url";
import UnoCSS from "unocss/astro";
const src = (p) => fileURLToPath(new URL(`./src/${p}`, import.meta.url));

export default defineConfig({
  integrations: [UnoCSS()],
  resolve: {
    alias: {
      "@": src(""),
    },
  },
});
