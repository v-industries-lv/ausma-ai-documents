import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import eslint from "vite-plugin-eslint";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), eslint()],
  server: {
    proxy: {
      "/api": "http://localhost:5000/",
      "/socket.io": {
        target: "ws://localhost:5000/",
        ws: true,
        rewriteWsOrigin: true,
      },
    },
  },
});
