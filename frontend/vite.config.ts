/// <reference types="vitest/config" />
import babel from "@rolldown/plugin-babel";
import react, { reactCompilerPreset } from "@vitejs/plugin-react";
import { resolve } from "node:path";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), babel({ presets: [reactCompilerPreset()] })],
  resolve: {
    alias: {
      "@": resolve(import.meta.dirname, "src"),
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text"],
      include: ["src/**/*.{ts,tsx}"],
      // The entry point only mounts <App /> in a real browser document; it has
      // no branch a test could exercise.
      exclude: ["src/main.tsx"],
    },
  },
});
