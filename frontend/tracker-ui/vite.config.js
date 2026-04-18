import { defineConfig } from 'vite'
import { resolve } from 'node:path'

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        about: resolve(__dirname, 'about.html'),
        index: resolve(__dirname, 'index.html'),
        login: resolve(__dirname, 'login.html'),
        product: resolve(__dirname, 'product.html'),
        register: resolve(__dirname, 'register.html'),
        profile: resolve(__dirname, 'profile.html'),
      },
    },
  },
})
