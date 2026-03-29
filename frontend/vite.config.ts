import path from "node:path";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiUrl = env.VITE_API_URL ?? "http://localhost:8000";

  return {
    plugins: [
      react(),
      VitePWA({
        registerType: "autoUpdate",
        manifest: {
          name: "Вахты и табель",
          short_name: "Табель",
          start_url: "/",
          display: "standalone",
          background_color: "#0f172a",
          theme_color: "#0f172a",
          lang: "ru",
        },
      }),
    ],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "src"),
      },
    },
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: apiUrl,
          changeOrigin: true,
        },
        "/health": {
          target: apiUrl,
          changeOrigin: true,
        },
      },
    },
  };
});
