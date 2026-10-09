// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  // Desactivado: evita cargar simple-git (ver "Seguridad de dependencias" en el README).
  devtools: { enabled: false },
  // Workaround for Nuxt 4.6.0 on Windows (nuxt/nuxt#36467): bundle the renderer
  // with a separator-agnostic pattern so SSR pages don't return 500.
  nitro: {
    externals: { inline: [/[\\/]node_modules[\\/]nuxt[\\/]dist[\\/]/] }
  },
  runtimeConfig: {
    public: {
      // Se sobrescriben con NUXT_PUBLIC_API_BASE, NUXT_PUBLIC_API_TIMEOUT_MS
      // y NUXT_PUBLIC_DEMO_MODE (ver .env.example).
      apiBase: 'http://127.0.0.1:8000',
      apiTimeoutMs: 60000,
      demoMode: true
    }
  }
})