import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    globals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text'],
      exclude: ['src/test/**', '**/*.test.jsx', '**/*.test.js'],
      // thresholds: {
      //   lines: 50,
      //   functions: 50,
      //   branches: 40,
      // },
    },
  },
})
