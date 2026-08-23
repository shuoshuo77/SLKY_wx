import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    port: 5174,
    proxy: {
      "/api/coze": "http://127.0.0.1:3001",
      "/api": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true
      },
      "/uploads": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true
      }
    }
  }
})
