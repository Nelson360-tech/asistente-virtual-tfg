import { onBeforeUnmount, onMounted, ref } from 'vue'

export interface VoiceRecorderOptions {
  maxSeconds?: number
  minMilliseconds?: number
}

export function useVoiceRecorder(options: VoiceRecorderOptions = {}) {
  const maxSeconds = options.maxSeconds ?? 60
  const minMilliseconds = options.minMilliseconds ?? 500

  const isRecording = ref(false)
  const isSupported = ref(true)
  const error = ref('')
  const recordedAudioUrl = ref<string | null>(null)
  const recordedBlob = ref<Blob | null>(null)

  let mediaRecorder: MediaRecorder | null = null
  let stream: MediaStream | null = null
  let chunks: Blob[] = []
  let startedAt = 0
  let limitTimer: ReturnType<typeof setTimeout> | null = null
  let starting = false
  let disposed = false

  function clearLimitTimer() {
    if (limitTimer) {
      clearTimeout(limitTimer)
      limitTimer = null
    }
  }

  function releaseMicrophone() {
    stream?.getTracks().forEach(track => track.stop())
    stream = null
  }

  function clearRecording() {
    if (recordedAudioUrl.value) {
      URL.revokeObjectURL(recordedAudioUrl.value)
      recordedAudioUrl.value = null
    }
    recordedBlob.value = null
  }

  function detach(recorder: MediaRecorder) {
    recorder.ondataavailable = null
    recorder.onstop = null
    recorder.onerror = null
  }

  function microphoneErrorMessage(err: unknown): string {
    const name = err instanceof DOMException ? err.name : ''

    if (name === 'NotAllowedError' || name === 'SecurityError') {
      return 'Permiso de micrófono denegado. Actívalo en el navegador.'
    }
    if (name === 'NotFoundError' || name === 'OverconstrainedError') {
      return 'No se ha encontrado ningún micrófono.'
    }
    if (name === 'NotReadableError' || name === 'AbortError') {
      return 'El micrófono está ocupado o no responde.'
    }
    return 'No se pudo acceder al micrófono.'
  }

  onMounted(() => {
    isSupported.value =
      !!navigator.mediaDevices?.getUserMedia &&
      typeof MediaRecorder !== 'undefined'
  })

  async function startRecording() {
    if (starting || isRecording.value || disposed) return

    error.value = ''

    if (
      typeof navigator === 'undefined' ||
      !navigator.mediaDevices?.getUserMedia ||
      typeof MediaRecorder === 'undefined'
    ) {
      isSupported.value = false
      error.value = 'Este navegador no permite grabar audio.'
      return
    }

    starting = true

    try {
      const newStream = await navigator.mediaDevices.getUserMedia({
        audio: true
      })

      // El componente se desmontó mientras se esperaba el permiso.
      if (disposed) {
        newStream.getTracks().forEach(track => track.stop())
        return
      }

      stream = newStream
      chunks = []
      clearRecording()

      const mimeType = [
        'audio/webm;codecs=opus',
        'audio/mp4',
        'audio/webm'
      ].find(type => MediaRecorder.isTypeSupported(type))

      const recorder = mimeType
        ? new MediaRecorder(newStream, { mimeType })
        : new MediaRecorder(newStream)

      mediaRecorder = recorder

      recorder.ondataavailable = event => {
        if (event.data.size > 0) {
          chunks.push(event.data)
        }
      }

      recorder.onstop = () => {
        clearLimitTimer()
        releaseMicrophone()
        isRecording.value = false

        const duration = Date.now() - startedAt
        const blob = new Blob(chunks, {
          type: recorder.mimeType || mimeType || 'audio/webm'
        })

        chunks = []
        mediaRecorder = null

        if (blob.size === 0 || duration < minMilliseconds) {
          error.value =
            'No se ha detectado audio. Mantén la grabación al menos un momento.'
          return
        }

        recordedBlob.value = blob
        recordedAudioUrl.value = URL.createObjectURL(blob)
      }

      recorder.onerror = () => {
        clearLimitTimer()
        detach(recorder)
        releaseMicrophone()
        chunks = []
        mediaRecorder = null
        isRecording.value = false
        error.value = 'Ha ocurrido un error durante la grabación.'
      }

      // Si el micrófono se desconecta, se cierra la grabación con lo captado.
      newStream.getAudioTracks().forEach(track => {
        track.addEventListener('ended', stopRecording, { once: true })
      })

      startedAt = Date.now()
      recorder.start()
      isRecording.value = true

      limitTimer = setTimeout(() => {
        error.value =
          `Se alcanzó el límite de ${maxSeconds} segundos. ` +
          'La grabación se ha detenido.'
        stopRecording()
      }, maxSeconds * 1000)
    } catch (err) {
      clearLimitTimer()
      if (mediaRecorder) detach(mediaRecorder)
      mediaRecorder = null
      releaseMicrophone()
      isRecording.value = false
      error.value = microphoneErrorMessage(err)
    } finally {
      starting = false
    }
  }

  function stopRecording() {
    clearLimitTimer()

    if (mediaRecorder?.state === 'recording') {
      mediaRecorder.stop()
    }
  }

  function toggleRecording() {
    if (isRecording.value) {
      stopRecording()
    } else {
      void startRecording()
    }
  }

  onBeforeUnmount(() => {
    disposed = true
    clearLimitTimer()

    if (mediaRecorder) {
      detach(mediaRecorder)
      if (mediaRecorder.state !== 'inactive') mediaRecorder.stop()
      mediaRecorder = null
    }

    releaseMicrophone()
    chunks = []
    clearRecording()
  })

  return {
    isRecording,
    isSupported,
    error,
    recordedAudioUrl,
    recordedBlob,
    maxSeconds,
    startRecording,
    stopRecording,
    toggleRecording
  }
}
