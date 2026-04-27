import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("markmap-view")) {
            return "markmap-view";
          }
          if (id.includes("markmap-lib")) {
            return "markmap-lib";
          }
          if (id.includes("katex") || id.includes("markdown-it-katex")) {
            return "markmap-katex";
          }
          if (id.includes("highlight.js") || id.includes("prismjs")) {
            return "markmap-highlight";
          }
          if (id.includes("\\yaml\\") || id.includes("/yaml/")) {
            return "markmap-yaml";
          }
          if (id.includes("d3-")) {
            return "markmap-d3";
          }
          if (id.includes("react-markdown") || id.includes("remark-gfm") || id.includes("mdast-util")) {
            return "markdown";
          }
          return undefined;
        },
      },
    },
  },
  server: {
    host: "127.0.0.1",
    port: 3015,
  },
});
