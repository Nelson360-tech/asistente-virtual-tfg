// Pruebas del cliente de la API sin el backend real.
// Un servidor HTTP local imita las respuestas documentadas en el README
// de la rama `backend-fastapi`. Ejecutar con: npm test
import { test, describe, before, after } from 'node:test'
import assert from 'node:assert/strict'
import { createServer, type IncomingMessage, type Server } from 'node:http'
import type { AddressInfo } from 'node:net'

import {
  askDonna,
  audioFileName,
  checkDonnaHealth,
  DonnaApiError,
  getDonnaAudioUrl,
  interpretDonnaResponse,
  parseSafeHttpUrl
} from '../app/services/donnaApi.ts'

const README_EXAMPLE = {
  question: '¿Qué hora es?',
  answer: 'Son las 18 horas con 19 minutos',
  audio_url: '/audio/a5544a8c.wav',
  visemes: [
    { start: 0.0, end: 0.133, viseme: 'sil' },
    { start: 0.133, end: 0.167, viseme: 'O' }
  ],
  action: null
}

const BASE = 'http://127.0.0.1:8000'

describe('audioFileName', () => {
  test('usa extensiones admitidas por el backend', () => {
    assert.equal(audioFileName('audio/webm;codecs=opus'), 'pregunta.webm')
    assert.equal(audioFileName('audio/webm'), 'pregunta.webm')
    assert.equal(audioFileName('audio/mp4'), 'pregunta.m4a')
    assert.equal(audioFileName('audio/mpeg'), 'pregunta.mp3')
    assert.equal(audioFileName('audio/wav'), 'pregunta.wav')
  })
})

describe('parseSafeHttpUrl', () => {
  test('acepta http y https', () => {
    assert.equal(parseSafeHttpUrl('https://example.com/a')?.href, 'https://example.com/a')
    assert.equal(parseSafeHttpUrl('http://example.com')?.hostname, 'example.com')
  })

  test('rechaza esquemas peligrosos, credenciales y valores no válidos', () => {
    assert.equal(parseSafeHttpUrl('javascript:alert(1)'), null)
    assert.equal(parseSafeHttpUrl('data:text/html,<script>x</script>'), null)
    assert.equal(parseSafeHttpUrl('file:///etc/passwd'), null)
    assert.equal(parseSafeHttpUrl('https://user:pass@example.com'), null)
    assert.equal(parseSafeHttpUrl('no es una url'), null)
    assert.equal(parseSafeHttpUrl(''), null)
    assert.equal(parseSafeHttpUrl(undefined), null)
    assert.equal(parseSafeHttpUrl(42), null)
  })
})

describe('getDonnaAudioUrl', () => {
  test('resuelve la ruta relativa respecto al backend', () => {
    assert.equal(
      getDonnaAudioUrl('/audio/a5544a8c.wav', BASE),
      'http://127.0.0.1:8000/audio/a5544a8c.wav'
    )
  })

  test('rechaza otros orígenes y esquemas', () => {
    assert.throws(() => getDonnaAudioUrl('https://evil.example/x.wav', BASE), DonnaApiError)
    assert.throws(() => getDonnaAudioUrl('javascript:alert(1)', BASE), DonnaApiError)
  })
})

describe('interpretDonnaResponse', () => {
  test('interpreta el ejemplo del README', () => {
    const turn = interpretDonnaResponse(README_EXAMPLE, BASE)
    assert.equal(turn.question, '¿Qué hora es?')
    assert.equal(turn.answer, 'Son las 18 horas con 19 minutos')
    assert.equal(turn.audioUrl, 'http://127.0.0.1:8000/audio/a5544a8c.wav')
    assert.deepEqual(turn.visemes, README_EXAMPLE.visemes)
    assert.equal(turn.openUrl, null)
    assert.deepEqual(turn.warnings, [])
  })

  test('acepta una acción open_url segura', () => {
    const turn = interpretDonnaResponse(
      { ...README_EXAMPLE, action: { type: 'open_url', url: 'https://www.youtube.com' } },
      BASE
    )
    assert.equal(turn.openUrl?.href, 'https://www.youtube.com/')
    assert.deepEqual(turn.warnings, [])
  })

  test('bloquea una acción open_url peligrosa', () => {
    const turn = interpretDonnaResponse(
      { ...README_EXAMPLE, action: { type: 'open_url', url: 'javascript:alert(1)' } },
      BASE
    )
    assert.equal(turn.openUrl, null)
    assert.equal(turn.warnings.length, 1)
  })

  test('ignora visemas mal formados', () => {
    const turn = interpretDonnaResponse(
      { ...README_EXAMPLE, visemes: [{ start: 0, end: 1, viseme: 'aa' }, { start: 'x' }] as never },
      BASE
    )
    assert.deepEqual(turn.visemes, [{ start: 0, end: 1, viseme: 'aa' }])
  })

  test('avisa si faltan pregunta y respuesta', () => {
    const turn = interpretDonnaResponse({}, BASE)
    assert.equal(turn.question, null)
    assert.equal(turn.answer, null)
    assert.equal(turn.warnings.length, 1)
  })
})

describe('askDonna contra un servidor de prueba', () => {
  let server: Server
  let base: string
  let lastRequest: { method?: string; url?: string; contentType?: string; body: string } | null = null

  function readBody(req: IncomingMessage): Promise<string> {
    return new Promise(resolve => {
      const parts: Buffer[] = []
      req.on('data', chunk => parts.push(chunk))
      req.on('end', () => resolve(Buffer.concat(parts).toString('latin1')))
    })
  }

  before(async () => {
    server = createServer(async (req, res) => {
      const body = await readBody(req)
      lastRequest = { method: req.method, url: req.url, contentType: req.headers['content-type'], body }
      if (req.url === '/health') {
        res.setHeader('content-type', 'application/json')
        res.end(JSON.stringify({ status: 'ok' }))
        return
      }

      if (req.url === '/api/ask') {
        res.setHeader('content-type', 'application/json')
        res.end(JSON.stringify(README_EXAMPLE))
      } else {
        res.statusCode = 404
        res.end()
      }
    })
    await new Promise<void>(resolve => server.listen(0, '127.0.0.1', resolve))
    base = `http://127.0.0.1:${(server.address() as AddressInfo).port}`
  })

  after(() => {
    server.closeAllConnections()
    server.close()
  })

  test('envía POST /api/ask con FormData y el campo audio', async () => {
    const blob = new Blob([new Uint8Array([1, 2, 3])], { type: 'audio/mp4' })
    const result = await askDonna(blob, { baseUrl: base })

    assert.equal(lastRequest?.method, 'POST')
    assert.equal(lastRequest?.url, '/api/ask')
    assert.match(lastRequest?.contentType ?? '', /^multipart\/form-data; boundary=/)
    assert.match(lastRequest?.body ?? '', /name="audio"; filename="pregunta\.m4a"/)
    assert.deepEqual(result, README_EXAMPLE)
  })

  test('checkDonnaHealth devuelve true si /health responde ok', async () => {
    assert.equal(await checkDonnaHealth(base), true)
  })
})

describe('askDonna: errores', () => {
  const servers: Server[] = []

  async function serve(handler: Parameters<typeof createServer>[1]): Promise<string> {
    const server = createServer(handler)
    servers.push(server)
    await new Promise<void>(resolve => server.listen(0, '127.0.0.1', resolve))
    return `http://127.0.0.1:${(server.address() as AddressInfo).port}`
  }

  after(() => {
    for (const s of servers) {
      s.closeAllConnections()
      s.close()
    }
  })

  const blob = new Blob([new Uint8Array([1])], { type: 'audio/webm' })

  async function expectKind(promise: Promise<unknown>, kind: string) {
    await assert.rejects(promise, (err: unknown) => {
      assert.ok(err instanceof DonnaApiError)
      assert.equal(err.kind, kind)
      return true
    })
  }

  test('error HTTP con detail de FastAPI', async () => {
    const base = await serve((_req, res) => {
      res.statusCode = 400
      res.setHeader('content-type', 'application/json')
      res.end(JSON.stringify({ detail: 'Formato de audio no admitido' }))
    })
    await assert.rejects(askDonna(blob, { baseUrl: base }), (err: unknown) => {
      assert.ok(err instanceof DonnaApiError)
      assert.equal(err.kind, 'server')
      assert.equal(err.status, 400)
      assert.equal(err.message, 'Formato de audio no admitido')
      return true
    })
  })

  test('error HTTP sin cuerpo JSON', async () => {
    const base = await serve((_req, res) => {
      res.statusCode = 500
      res.end('Internal Server Error')
    })
    await assert.rejects(askDonna(blob, { baseUrl: base }), (err: unknown) => {
      assert.ok(err instanceof DonnaApiError)
      assert.equal(err.kind, 'server')
      assert.match(err.message, /código 500/)
      return true
    })
  })

  test('respuesta que no es JSON', async () => {
    const base = await serve((_req, res) => res.end('<html>no json</html>'))
    await expectKind(askDonna(blob, { baseUrl: base }), 'invalid-response')
  })

  test('respuesta JSON que no es un objeto', async () => {
    const base = await serve((_req, res) => res.end('[1,2,3]'))
    await expectKind(askDonna(blob, { baseUrl: base }), 'invalid-response')
  })

  test('tiempo de espera agotado', async () => {
    const base = await serve(() => { /* nunca responde */ })
    await expectKind(askDonna(blob, { baseUrl: base, timeoutMs: 150 }), 'timeout')
  })

  test('cancelación desde fuera', async () => {
    const base = await serve(() => { /* nunca responde */ })
    const controller = new AbortController()
    const promise = askDonna(blob, { baseUrl: base, signal: controller.signal })
    setTimeout(() => controller.abort(), 50)
    await expectKind(promise, 'cancelled')
  })

  test('servidor apagado', async () => {
    const base = await serve(() => {})
    const server = servers.pop()!
    await new Promise(resolve => server.close(resolve))
    await expectKind(askDonna(blob, { baseUrl: base }), 'network')
    assert.equal(await checkDonnaHealth(base, 500), false)
  })
})
