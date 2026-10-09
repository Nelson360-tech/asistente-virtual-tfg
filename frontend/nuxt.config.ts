// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  // Desactivado: evita cargar simple-git (ver "Seguridad de dependencias" en el README).
  devtools: { enabled: false },
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
