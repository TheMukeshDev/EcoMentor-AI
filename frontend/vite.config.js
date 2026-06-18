import { defineConfig } from 'vite';

export default defineConfig({
  publicDir: 'public',
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsInlineLimit: 4096,
  },
});
