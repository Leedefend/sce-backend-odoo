import { defineConfig } from "vite";
import uniModule from "@dcloudio/vite-plugin-uni";

const uni = (uniModule as unknown as { default?: typeof uniModule }).default ?? uniModule;

export default defineConfig({
  plugins: [uni()],
});
