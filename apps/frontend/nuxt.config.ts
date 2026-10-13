// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  css: ["~/assets/css/main.css"],

  nitro: {
    preset: "bun",
    devServer: {
      watch: ["server/**/*"]
    }
  },
  modules: ['@nuxt/eslint', '@nuxt/image', '@nuxt/ui'],

  routeRules: {
      '/ml/**': {
          proxy: { to: "http://127.0.0.1:3001/**", },
      }
    }
})