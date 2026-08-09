import { defineConfig } from "vite";
import pkg from "./package.json";

export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/matrix": "http://127.0.0.1:8000",
      "^/health$": "http://127.0.0.1:8000",
      "^/version$": "http://127.0.0.1:8000",
    },
  },
});
