import { defineConfig } from 'vite'

// Express API runs on PORT (default 3000); Vite dev serves the SPA on 5173
// and proxies auth + data endpoints so the session cookie flows through.
const API_TARGET = `http://localhost:${process.env.API_PORT || 3000}`

export default defineConfig({
  root: '.',
  publicDir: 'public',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/login':   { target: API_TARGET, changeOrigin: false },
      '/logout':  { target: API_TARGET, changeOrigin: false },
      '/data':    { target: API_TARGET, changeOrigin: false },
      '/auth':    { target: API_TARGET, changeOrigin: false },
    },
  },
})
