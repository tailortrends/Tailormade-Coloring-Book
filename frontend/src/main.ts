import { createApp } from 'vue'
import { createPinia } from 'pinia'
import VueKonva from 'vue-konva'
import { MotionPlugin } from '@vueuse/motion'
import * as Sentry from '@sentry/vue'

import App from './App.vue'
import router from './router'
import './assets/styles/main.css'

const app = createApp(App)

// ── Sentry Initialization ─────────────────────────────────────────────────────
if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    app,
    dsn: import.meta.env.VITE_SENTRY_DSN,
    integrations: [
      Sentry.browserTracingIntegration({ router }),
      Sentry.replayIntegration(),
    ],
    tracesSampleRate: 1.0,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
  })
}

// ── Global Error Handler ──────────────────────────────────────────────────────
// Catches unhandled errors in any component to prevent white-screen crashes
app.config.errorHandler = (err, instance, info) => {
  console.error('[TailorMade] Unhandled error:', err)
  console.error('[TailorMade] Component:', instance?.$options?.name || 'unknown')
  console.error('[TailorMade] Info:', info)
  
  if (import.meta.env.VITE_SENTRY_DSN) {
    Sentry.captureException(err, {
      extra: {
        component: instance?.$options?.name,
        info,
      },
    })
  }
}

app.use(createPinia())
app.use(router)
app.use(VueKonva)
app.use(MotionPlugin)

app.mount('#app')
