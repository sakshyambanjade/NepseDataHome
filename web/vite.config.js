import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const base = '/NepseDataHome/';

export default defineConfig({
  plugins: [react()],
  base: base,
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
