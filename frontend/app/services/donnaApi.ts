// Contrato documentado en el README de la rama `backend-fastapi`:
// POST /api/ask (FormData, campo `audio`; webm, m4a, mp3 o wav)
// → { question, answer, audio_url, visemes, action }

export interface DonnaViseme {
  start: number
  end: number
  viseme: string
}

export interface DonnaAction {
  type: string
  url?: string
}

export interface DonnaResponse {
  question?: string
  answer?: string
  audio_url?: string
  visemes?: DonnaViseme[]
  action?: DonnaAction | null
}

export interface DonnaRequestOptions {
  baseUrl: string
  timeoutMs?: number
  signal?: AbortSignal
}

export type DonnaErrorKind =
  | 'timeout'
  | 'cancelled'
  | 'network'
  | 'server'
  | 'invalid-response'

export class DonnaApiError extends Error {
  kind: DonnaErrorKind
  status?: number

  constructor(kind: DonnaErrorKind, message: string, status?: number) {
    super(message)
    this.name = 'DonnaApiError'
    this.kind = kind
    this.status = status
  }
}

const DEFAULT_TIMEOUT_MS = 60000

/**
 * Nombre de archivo con una extensión que admite el backend.
 * Safari graba en audio/mp4, que se envía como .m4a (mismo contenedor).
 */
export function audioFileName(mimeType: string): string {
  const type = mimeType.toLowerCase()

  if (type.includes('mp4') || type.includes('m4a') || type.includes('aac')) {
    return 'pregunta.m4a'
  }
  if (type.includes('mpeg') || type.includes('mp3')) return 'pregunta.mp3'
  if (type.includes('wav')) return 'pregunta.wav'
  return 'pregunta.webm'
}

async function serverErrorMessage(response: Response): Promise<string> {
  try {
    const data: unknown = await response.json()
    // Formato estándar de errores de FastAPI: { "detail": "..." }
    if (
      typeof data === 'object' && data !== null &&
      typeof (data as { detail?: unknown }).detail === 'string'
    ) {
      return (data as { detail: string }).detail
    }
  } catch {
    // Cuerpo vacío o no JSON: se usa el mensaje genérico.
  }
  return `El servidor no pudo procesar la petición (código ${response.status}).`
}

export async function askDonna(
  blob: Blob,
  options: DonnaRequestOptions
): Promise<DonnaResponse> {
  const formData = new FormData()
  formData.append('audio', blob, audioFileName(blob.type))

  const controller = new AbortController()
  let timedOut = false
  const timer = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, options.timeoutMs ?? DEFAULT_TIMEOUT_MS)

  const onExternalAbort = () => controller.abort()
  if (options.signal?.aborted) controller.abort()
  options.signal?.addEventListener('abort', onExternalAbort)

  const abortError = () => timedOut
    ? new DonnaApiError(
        'timeout',
        'Donna tarda demasiado en responder. Inténtalo de nuevo.'
      )
    : new DonnaApiError('cancelled', 'Petición cancelada.')

  try {
    let response: Response

    try {
      response = await fetch(new URL('/api/ask', options.baseUrl), {
        method: 'POST',
        body: formData,
        signal: controller.signal
      })
    } catch {
      if (controller.signal.aborted) throw abortError()
      throw new DonnaApiError(
        'network',
        'No se pudo conectar con el servidor de Donna. ' +
        'Comprueba que está en marcha.'
      )
    }

    if (!response.ok) {
      throw new DonnaApiError(
        'server',
        await serverErrorMessage(response),
        response.status
      )
    }

    let data: unknown
    try {
      data = await response.json()
    } catch {
      if (controller.signal.aborted) throw abortError()
      throw new DonnaApiError(
        'invalid-response',
        'La respuesta del servidor no tiene un formato válido.'
      )
    }

    if (typeof data !== 'object' || data === null || Array.isArray(data)) {
      throw new DonnaApiError(
        'invalid-response',
        'La respuesta del servidor no tiene un formato válido.'
      )
    }

    return data as DonnaResponse
  } finally {
    clearTimeout(timer)
    options.signal?.removeEventListener('abort', onExternalAbort)
  }
}

/** Comprueba GET /health. Devuelve true si el backend responde "ok". */
export async function checkDonnaHealth(
  baseUrl: string,
  timeoutMs = 3000
): Promise<boolean> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(new URL('/health', baseUrl), {
      signal: controller.signal
    })
    if (!response.ok) return false
    const data = await response.json() as { status?: unknown }
    return data?.status === 'ok'
  } catch {
    return false
  } finally {
    clearTimeout(timer)
  }
}

/**
 * Devuelve la URL solo si es http(s) y no incluye credenciales.
 * Devuelve null en cualquier otro caso (esquema peligroso, URL mal formada…).
 */
export function parseSafeHttpUrl(raw: unknown): URL | null {
  if (typeof raw !== 'string' || raw.trim() === '') return null

  let url: URL
  try {
    url = new URL(raw.trim())
  } catch {
    return null
  }

  if (!['http:', 'https:'].includes(url.protocol)) return null
  if (url.username || url.password) return null

  return url
}

/**
 * Resuelve `audio_url` (ruta relativa, p. ej. /audio/xxx.wav) respecto al
 * backend. Solo se admiten URLs http(s) del mismo origen que la API.
 */
export function getDonnaAudioUrl(path: string, baseUrl: string): string {
  const base = new URL(baseUrl)
  let url: URL

  try {
    url = new URL(path, base)
  } catch {
    throw new DonnaApiError('invalid-response', 'La URL del audio no es válida.')
  }

  if (!['http:', 'https:'].includes(url.protocol) || url.origin !== base.origin) {
    throw new DonnaApiError('invalid-response', 'La URL del audio no es válida.')
  }

  return url.href
}

function parseVisemes(raw: unknown): DonnaViseme[] {
  if (!Array.isArray(raw)) return []

  return raw.filter((item): item is DonnaViseme =>
    typeof item === 'object' && item !== null &&
    Number.isFinite(item.start) &&
    Number.isFinite(item.end) &&
    typeof item.viseme === 'string'
  )
}

export interface DonnaTurn {
  question: string | null
  answer: string | null
  audioUrl: string | null
  visemes: DonnaViseme[]
  openUrl: URL | null
  warnings: string[]
}

/** Convierte la respuesta del backend en datos listos para la interfaz. */
export function interpretDonnaResponse(
  data: DonnaResponse,
  baseUrl: string
): DonnaTurn {
  const warnings: string[] = []
  const text = (value: unknown) =>
    typeof value === 'string' && value.trim() ? value.trim() : null

  const question = text(data.question)
  const answer = text(data.answer)

  let audioUrl: string | null = null
  if (typeof data.audio_url === 'string' && data.audio_url) {
    try {
      audioUrl = getDonnaAudioUrl(data.audio_url, baseUrl)
    } catch {
      warnings.push('No se pudo cargar el audio de la respuesta.')
    }
  }

  let openUrl: URL | null = null
  if (data.action?.type === 'open_url') {
    openUrl = parseSafeHttpUrl(data.action.url)
    if (!openUrl) {
      warnings.push(
        'Donna ha solicitado abrir una dirección no válida y se ha bloqueado.'
      )
    }
  }

  if (!question && !answer) {
    warnings.push('El servidor respondió, pero sin pregunta ni respuesta.')
  }

  return {
    question,
    answer,
    audioUrl,
    visemes: parseVisemes(data.visemes),
    openUrl,
    warnings
  }
}
