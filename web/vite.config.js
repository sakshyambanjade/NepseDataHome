import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const isProd = process.env.NODE_ENV === 'production';
const base = isProd ? `/${process.env.VITE_BASE_PATH || ''}/` : '/';

export default defineConfig({
  plugins: [react()],
  base: base,
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
