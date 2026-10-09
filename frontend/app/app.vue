<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount, onMounted, provide } from 'vue'
import {
  askDonna,
  checkDonnaHealth,
  interpretDonnaResponse,
  DonnaApiError,
  type DonnaViseme
} from './services/donnaApi'
import { donnaAvatarKey } from './composables/useDonnaAvatar'

const config = useRuntimeConfig()
const apiBase = String(config.public.apiBase)
const apiTimeoutMs = Number(config.public.apiTimeoutMs) || 60000

type Theme = 'futuristic' | 'modern' | 'minimal'

const theme = ref<Theme>('futuristic')

const {
  isRecording,
  error,
  recordedAudioUrl,
  recordedBlob,
  toggleRecording
} = useVoiceRecorder()

const themes: { id: Theme; label: string }[] = [
  { id: 'futuristic', label: 'Futurista' },
  { id: 'modern', label: 'Moderno' },
  { id: 'minimal', label: 'Minimalista' }
]

type Message = {
  id: number
  role: 'user' | 'assistant'
  text: string
}

const messages = ref<Message[]>([
  {
    id: 1,
    role: 'assistant',
    text: 'Hola, ¿en qué puedo ayudarte hoy?'
  }
])

const chatStatus = ref('Lista para hablar')
const processing = ref(false)
const chatContainer = ref<HTMLElement | null>(null)
let nextMessageId = 2

function addMessage(role: Message['role'], text: string) {
  messages.value.push({
    id: nextMessageId++,
    role,
    text
  })

  void nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop =
        chatContainer.value.scrollHeight
    }
  })
}

const demoMode = ref(
  config.public.demoMode !== false && String(config.public.demoMode) !== 'false'
)
const donnaAudioUrl = ref<string | null>(null)
const donnaAudio = ref<HTMLAudioElement | null>(null)
const audioBlocked = ref(false)
const speaking = ref(false)
const visemes = ref<DonnaViseme[]>([])
const pendingUrl = ref<string | null>(null)
const pendingUrlHost = ref('')
const integrationError = ref('')
const backendStatus = ref<'checking' | 'online' | 'offline'>('checking')
let requestController: AbortController | null = null

provide(donnaAvatarKey, {
  audio: donnaAudio,
  visemes,
  speaking,
  listening: isRecording,
  processing
})

// Audio mínimo y silencioso. Se reproduce durante el gesto del usuario
// (clic en "Hablar") para que Safari permita reproducir la respuesta después.
const SILENT_WAV =
  'data:audio/wav;base64,UklGRiYAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQIAAAAAAA=='

function unlockAudio() {
  const el = donnaAudio.value
  if (!el) return
  el.pause()
  el.src = SILENT_WAV
  void el.play().catch(() => {})
}

function onMicClick() {
  if (!isRecording.value) {
    donnaAudioUrl.value = null
    audioBlocked.value = false
    unlockAudio()
  }
  toggleRecording()
}

async function playResponseAudio() {
  await nextTick()
  const el = donnaAudio.value
  if (!el || !donnaAudioUrl.value) return

  try {
    await el.play()
    audioBlocked.value = false
  } catch {
    // Autoplay bloqueado (p. ej. Safari): quedan los controles manuales.
    audioBlocked.value = true
  }
}

watch(donnaAudioUrl, url => {
  if (url) void playResponseAudio()
})

function onAudioPlay() {
  // El audio silencioso de desbloqueo no cuenta como respuesta.
  speaking.value = !!donnaAudioUrl.value
  if (speaking.value) audioBlocked.value = false
}

function onAudioStop() {
  speaking.value = false
}

/**
 * Abre la URL en otra pestaña sin dar acceso a esta ventana.
 * Devuelve false si el navegador bloquea la ventana emergente.
 */
function openInNewTab(url: string): boolean {
  const tab = window.open('about:blank', '_blank')
  if (!tab) return false

  try {
    tab.opener = null
    tab.location.href = url
    return true
  } catch {
    tab.close()
    return false
  }
}

async function refreshBackendStatus() {
  if (demoMode.value) return
  backendStatus.value = 'checking'
  backendStatus.value = await checkDonnaHealth(apiBase)
    ? 'online'
    : 'offline'
}

async function handleRecording(blob: Blob) {
  if (processing.value) return

  processing.value = true
  chatStatus.value = 'Procesando…'
  integrationError.value = ''
  audioBlocked.value = false
  donnaAudioUrl.value = null
  visemes.value = []
  pendingUrl.value = null
  pendingUrlHost.value = ''
  requestController = new AbortController()

  try {
    if (demoMode.value) {
      addMessage('user', '¿Qué hora es?')

      await new Promise(resolve => setTimeout(resolve, 500))

      addMessage(
        'assistant',
        'Respuesta simulada. En modo real, Donna ' +
        'transcribirá y responderá a tu grabación.'
      )
    } else {
      const result = await askDonna(blob, {
        baseUrl: apiBase,
        timeoutMs: apiTimeoutMs,
        signal: requestController.signal
      })
      backendStatus.value = 'online'

      const turn = interpretDonnaResponse(result, apiBase)

      if (turn.question) addMessage('user', turn.question)
      if (turn.answer) addMessage('assistant', turn.answer)

      visemes.value = turn.visemes
      donnaAudioUrl.value = turn.audioUrl

      if (turn.openUrl && !openInNewTab(turn.openUrl.href)) {
        // Ventana emergente bloqueada: se ofrece el botón alternativo.
        pendingUrl.value = turn.openUrl.href
        pendingUrlHost.value = turn.openUrl.hostname
      }

      if (turn.warnings.length) {
        integrationError.value = turn.warnings.join(' ')
      }
    }
  } catch (error) {
    if (error instanceof DonnaApiError && error.kind === 'cancelled') return
    if (error instanceof DonnaApiError && error.kind === 'network') {
      backendStatus.value = 'offline'
    }
    integrationError.value =
      error instanceof Error ? error.message : 'Ha ocurrido un error inesperado.'
  } finally {
    requestController = null
    processing.value = false
    chatStatus.value = 'Lista para hablar'
  }
}

function openPendingUrl() {
  if (!pendingUrl.value) return
  if (openInNewTab(pendingUrl.value)) {
    pendingUrl.value = null
    pendingUrlHost.value = ''
  }
}

const connectionLabel = {
  checking: 'Comprobando conexión con FastAPI…',
  online: 'Conectado a FastAPI',
  offline: 'Servidor FastAPI no disponible'
} as const

onMounted(() => void refreshBackendStatus())
watch(demoMode, () => void refreshBackendStatus())

onBeforeUnmount(() => requestController?.abort())

watch(recordedBlob, blob => {
  if (blob) void handleRecording(blob)
})

useHead({
  title: 'Donna | Asistente virtual por voz',
  meta: [{
    name: 'description',
    content: 'Donna, asistente personal inteligente por voz'
  }]
})
</script>

<template>
  <main class="donna" :data-theme="theme">
    <div class="shell">
      <header class="header">
        <div class="brand">
          <span class="brand-icon">✳</span>
          <h1>Donna<span>.</span></h1>
        </div>

        <div class="header-actions">
          <div class="status" role="status" aria-live="polite">
            <span class="status-dot"></span>
            {{ isRecording ? 'Escuchando…' : chatStatus }}
          </div>

          <div class="theme-switcher" role="group" aria-label="Estilo visual">
            <button
              v-for="item in themes"
              :key="item.id"
              type="button"
              :class="{ active: theme === item.id }"
              :aria-pressed="theme === item.id"
              @click="theme = item.id"
            >
              {{ item.label }}
            </button>
          </div>
        </div>
      </header>

      <div class="workspace">
        <section class="voice-panel" aria-label="Asistente de voz">
          <!-- Contenedor del avatar 3D: el componente se monta aquí y
               obtiene audio, visemas y estados con useDonnaAvatar(). -->
          <div
            id="donna-avatar"
            class="avatar-placeholder"
            :data-speaking="speaking"
            :data-listening="isRecording"
            :data-processing="processing"
          >
            <div class="voice-symbol">
              <svg viewBox="0 0 48 48" fill="none" aria-hidden="true"
                   stroke="currentColor" stroke-width="2.8"
                   stroke-linecap="round">
                <path d="M8 20v8M14 14v20M20 9v30M26 17v14M32 11v26M38 20v8"/>
              </svg>
            </div>
            <p class="avatar-caption">Espacio para el avatar de Donna</p>
          </div>

          <div class="voice-bottom">
            <h2>¿En qué puedo ayudarte?</h2>
            <p>Haz una pregunta usando tu voz.</p>

            <button
              class="mic-button"
              type="button"
              :class="{ recording: isRecording }"
              :disabled="processing"
              @click="onMicClick"
            >
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"
                   stroke="currentColor" stroke-width="1.8"
                   stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="2" width="6" height="12" rx="3"/>
                <path d="M5 10a7 7 0 0 0 14 0M12 17v5M8 22h8"/>
              </svg>
              {{ isRecording ? 'Detener grabación' : 'Hablar' }}
            </button>

            <p v-if="error" class="recording-error" role="alert">
              {{ error }}
            </p>

            <div v-if="recordedAudioUrl" class="audio-preview">
              <p>Tu última grabación</p>
              <audio :src="recordedAudioUrl" controls />
            </div>
          </div>
        </section>

        <section class="chat-panel" aria-label="Conversación">
          <div class="chat-header">
            <h2>Conversación</h2>
            <div class="api-mode">
              <label for="demo-mode">Modo demo</label>
              <input id="demo-mode" v-model="demoMode"
                     type="checkbox" :disabled="processing">
            </div>
          </div>

          <div
            ref="chatContainer"
            class="chat-messages"
            role="log"
            aria-live="polite"
            aria-relevant="additions"
            aria-label="Mensajes de la conversación"
          >
            <div
              v-for="message in messages"
              :key="message.id"
              class="message"
              :class="message.role"
            >
              <span class="sr-only">
                {{ message.role === 'user' ? 'Tú: ' : 'Donna: ' }}
              </span>
              {{ message.text }}
            </div>
          </div>

          <div class="chat-footer">
            <p v-if="integrationError" class="api-error" role="alert">
              {{ integrationError }}
            </p>

            <p v-if="audioBlocked" class="audio-hint">
              Tu navegador ha bloqueado la reproducción automática.
              Pulsa play para escuchar la respuesta.
            </p>

            <audio
              v-show="donnaAudioUrl"
              ref="donnaAudio"
              :src="donnaAudioUrl ?? undefined"
              controls
              playsinline
              preload="auto"
              class="donna-audio"
              aria-label="Respuesta de Donna en audio"
              @play="onAudioPlay"
              @pause="onAudioStop"
              @ended="onAudioStop"
            />

            <button
              v-if="pendingUrl"
              type="button"
              class="url-button"
              :aria-label="`Abrir página solicitada: ${pendingUrlHost}`"
              :title="pendingUrlHost"
              @click="openPendingUrl"
            >
              Abrir página solicitada ↗
            </button>

            <span role="status">
              {{
                processing
                  ? 'Donna está procesando…'
                  : demoMode ? 'Modo demostración' : connectionLabel[backendStatus]
              }}
            </span>
          </div>
        </section>
      </div>

      <footer class="footer">
        Donna © 2026
      </footer>
    </div>
  </main>
</template>

<style>
* {
  box-sizing: border-box;
}

html, body, #__nuxt {
  margin: 0;
  min-height: 100%;
}

body {
  font-family: -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
}

button {
  font: inherit;
}

.donna {
  --bg: #0b0a12;
  --panel: #141020;
  --text: #f5f2fa;
  --muted: #b8adc8;
  --accent: #bb99f4;
  --accent-text: #211330;
  --border: #30283d;
  --bubble: #292037;

  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
}

.donna[data-theme="modern"] {
  --bg: #f3f5f9;
  --panel: #ffffff;
  --text: #18253a;
  --muted: #57667b;
  --accent: #7da8dc;
  --accent-text: #14243b;
  --border: #dbe2eb;
  --bubble: #eaf0f8;
}

.donna[data-theme="minimal"] {
  --bg: #f7f7f5;
  --panel: #ffffff;
  --text: #222222;
  --muted: #595959;
  --accent: #292929;
  --accent-text: #ffffff;
  --border: #dededb;
  --bubble: #f0f0ee;
}

.shell {
  width: min(1100px, 92%);
  margin: 0 auto;
  padding: 36px 0 24px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand h1 {
  margin: 0;
  font-size: 26px;
  letter-spacing: -1px;
  font-weight: 650;
}

.brand h1 span {
  color: var(--accent);
}

.brand-icon {
  color: var(--accent);
  font-size: 25px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 25px;
}

.status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 13px;
  white-space: nowrap;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #56ca8a;
}

.theme-switcher {
  display: flex;
  gap: 3px;
  padding: 4px;
  border: 1px solid var(--border);
  border-radius: 10px;
}

.theme-switcher button {
  border: 0;
  background: transparent;
  color: var(--muted);
  padding: 8px 11px;
  border-radius: 7px;
  cursor: pointer;
  font-size: 12px;
}

.theme-switcher button.active {
  background: var(--accent);
  color: var(--accent-text);
  font-weight: 600;
}

.workspace {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 22px;
  min-height: 530px;
}

.voice-panel,
.chat-panel {
  background: var(--panel);
  border-radius: 13px;
  min-width: 0;
}

.voice-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 28px;
  text-align: center;
}

.avatar-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.voice-symbol {
  width: 130px;
  height: 130px;
  border: 1px solid var(--border);
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--bubble);
  color: var(--accent);
}

.voice-symbol svg {
  width: 46px;
  height: 46px;
}

.avatar-caption {
  font-size: 12px;
  color: var(--muted);
  margin-top: 20px;
}

.voice-bottom {
  padding: 20px 0 12px;
}

.voice-bottom h2 {
  font-size: 21px;
  margin: 0;
  font-weight: 600;
}

.voice-bottom p {
  font-size: 13px;
  color: var(--muted);
  margin: 12px 0 22px;
}

.mic-button {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  background: var(--accent);
  color: var(--accent-text);
  border: 0;
  border-radius: 30px;
  padding: 13px 22px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.mic-button svg {
  width: 17px;
  height: 17px;
}

.mic-button:hover {
  filter: brightness(1.08);
}

.mic-button:focus-visible,
.url-button:focus-visible,
.theme-switcher button:focus-visible {
  outline: 3px solid var(--accent);
  outline-offset: 3px;
}

.chat-panel {
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.chat-header h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 20px;
}

.chat-messages {
  flex: 1;
}

.message {
  background: var(--bubble);
  padding: 16px;
  border-radius: 9px;
  font-size: 14px;
  line-height: 1.6;
}

.chat-footer {
  color: var(--muted);
  font-size: 13px;
  padding-top: 20px;
}

.footer {
  padding-top: 22px;
  color: var(--muted);
  font-size: 12px;
}

@media (max-width: 800px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    flex-wrap: wrap;
    justify-content: space-between;
  }

  .workspace {
    grid-template-columns: 1fr;
  }

  .voice-panel {
    min-height: 400px;
  }

  .chat-panel {
    min-height: 350px;
  }
}

@media (max-width: 400px) {
  .theme-switcher {
    flex-wrap: wrap;
  }
}

.mic-button.recording {
  background: #e87c9a;
  color: #21101a;
}

.recording-error {
  color: #ff9aaa !important;
}

.audio-preview {
  margin-top: 20px;
}

.audio-preview p {
  font-size: 13px;
  color: var(--muted);
}

.audio-preview audio {
  width: min(280px, 100%);
  max-width: 100%;
}


.chat-messages {
  overflow-y: auto;
  min-height: 0;
  max-height: 480px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
}

.message {
  max-width: 85%;
  overflow-wrap: anywhere;
}

.message.user {
  align-self: flex-end;
  background: var(--accent);
  color: var(--accent-text);
}

.message.assistant {
  align-self: flex-start;
}

.mic-button:disabled {
  opacity: .55;
  cursor: wait;
}


.api-mode {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: 12px;
  color: var(--muted);
  font-size: 12px;
}

.api-mode input {
  accent-color: var(--accent);
  width: 16px;
  height: 16px;
}

.api-error {
  color: #ff9da9;
  overflow-wrap: anywhere;
}

.donna-audio {
  display: block;
  width: 100%;
  margin-bottom: 15px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.audio-hint {
  margin: 0 0 12px;
  color: var(--muted);
}

.url-button {
  display: block;
  margin-bottom: 15px;
  background: var(--accent);
  color: var(--accent-text);
  border: none;
  border-radius: 9px;
  padding: 11px 16px;
  cursor: pointer;
}
</style>
