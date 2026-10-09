# Donna · Frontend

Interfaz web de **Donna**, un asistente virtual por voz. El usuario graba una pregunta con el micrófono, el frontend la envía al backend (FastAPI) y muestra la conversación, reproduce la respuesta en audio y puede abrir una página web cuando el backend lo solicita.

Esta carpeta contiene el frontend. El backend (FastAPI) está en la carpeta `backend` del mismo repositorio.

## Tecnologías

| Pieza | Uso |
| --- | --- |
| [Nuxt 4](https://nuxt.com) | Framework de la aplicación (estructura `app/`, configuración en tiempo de ejecución) |
| [Vue 3](https://vuejs.org) | Componentes, `<script setup>` y reactividad |
| TypeScript | Tipado de servicios y composables, comprobado con `vue-tsc` |
| MediaRecorder API | Grabación de audio en el navegador |
| Fetch + `FormData` | Comunicación con FastAPI |

Versiones instaladas al preparar esta documentación: Nuxt 4.6.0, Vue 3.5.43. Las versiones exactas están en `package-lock.json`.

## Estructura

```
app/
├── app.vue                      # Interfaz: panel de voz, chat, temas y modo demostración
├── components/
│   └── DonnaAvatar.client.vue   # Avatar 3D (Three.js) con sincronización labial
├── composables/
│   ├── useVoiceRecorder.ts      # Grabación con MediaRecorder
│   └── useDonnaAvatar.ts        # Datos compartidos con el avatar 3D
├── services/
│   └── donnaApi.ts              # Cliente HTTP de FastAPI y validación de URLs
└── utils/
    └── visemeMouth.ts           # Visemas → expresiones faciales ARKit
tests/
├── donnaApi.test.ts             # Pruebas del cliente de la API (node --test)
└── visemeMouth.test.ts          # Pruebas de la lógica de visemas
public/
├── models/facecap.glb           # Modelo 3D del avatar (ejemplo de Three.js)
└── basis/                       # Decodificador de texturas KTX2 de Three.js
nuxt.config.ts                   # Configuración de Nuxt y variables públicas
.env.example                     # Variables de entorno disponibles
```

## Arquitectura

```
Micrófono ─▶ useVoiceRecorder ─▶ Blob de audio ─▶ app.vue ─▶ donnaApi.askDonna ─▶ FastAPI
                                                       ▲                              │
              chat · audio · visemas (avatar) · open_url ◀────────────────────────────┘
```

### Grabación (`useVoiceRecorder`)

- Solicita el micrófono con `getUserMedia` y graba con `MediaRecorder`.
- Elige el primer formato soportado entre `audio/webm;codecs=opus`, `audio/mp4` y `audio/webm`. En Safari suele resultar `audio/mp4`.
- Duración máxima de 60 segundos: al alcanzarla, la grabación se detiene y se avisa al usuario.
- Las grabaciones vacías o de menos de 0,5 s se descartan con un mensaje.
- Libera el micrófono y las URLs de objeto al terminar, ante errores y al desmontar el componente.
- Distingue entre permiso denegado, micrófono no encontrado y micrófono ocupado.
- Requiere un contexto seguro: `localhost` o HTTPS.

### Interfaz de conversación (`app.vue`)

- Panel de voz con el botón de grabar y el **contenedor del avatar 3D** (`#donna-avatar`).
- Panel de conversación con la pregunta transcrita y la respuesta de Donna.
- Tres temas visuales seleccionables (Futurista, Moderno y Minimalista).
- **Modo demostración**: simula una respuesta sin llamar al backend. Con el modo desactivado no se simula nada: todo procede de FastAPI.
- Estado de conexión: en modo real se consulta `GET /health` y se indica si FastAPI está disponible.
- Audio: la respuesta se intenta reproducir automáticamente. Si el navegador lo bloquea (por ejemplo, Safari), aparece un aviso y quedan los controles manuales. Al pulsar "Hablar" se reproduce un audio silencioso para que Safari permita la reproducción posterior.
- Enlaces: con `action.type === "open_url"` se intenta abrir la URL en otra pestaña, sin acceso a esta ventana. Si el navegador bloquea la ventana emergente, aparece el botón "Abrir página solicitada".
- Accesibilidad: el chat es una región `role="log"` con anuncios `aria-live`, los estados son regiones `status` y cada mensaje indica quién habla para lectores de pantalla.

### Avatar 3D (`useDonnaAvatar`)

El componente del avatar se monta dentro de `#donna-avatar`, en lugar del icono provisional, y obtiene los datos con:

```ts
const { audio, visemes, speaking, listening, processing } = useDonnaAvatar()
```

| Dato | Uso |
| --- | --- |
| `audio` | Elemento `<audio>` de la respuesta; `audio.value.currentTime` permite sincronizar los visemas |
| `visemes` | Visemas de la última respuesta: `{ start, end, viseme }` (segundos, estándar Oculus) |
| `speaking` | Donna está reproduciendo la respuesta |
| `listening` | El usuario está grabando |
| `processing` | Se espera la respuesta del backend |

El contenedor también expone `data-speaking`, `data-listening` y `data-processing`.

### Conexión con FastAPI (`donnaApi.ts`)

Contrato según el README de la rama `backend-fastapi` del repositorio del equipo:

- `POST {NUXT_PUBLIC_API_BASE}/api/ask` con `multipart/form-data` y la grabación en el campo `audio`. Formatos admitidos por el backend: webm, m4a, mp3 y wav.
  - Chrome y Firefox envían `pregunta.webm`. Safari graba `audio/mp4` y se envía como `pregunta.m4a`.
- Respuesta:

  ```json
  {
    "question": "¿Qué hora es?",
    "answer": "Son las 18 horas con 19 minutos",
    "audio_url": "/audio/a5544a8c....wav",
    "visemes": [{ "start": 0.0, "end": 0.133, "viseme": "sil" }],
    "action": null
  }
  ```

  - `audio_url` es una ruta relativa: se resuelve contra `NUXT_PUBLIC_API_BASE` y solo se acepta del mismo origen.
  - `action` es `null` o `{ "type": "open_url", "url": "..." }`. Solo se abren URLs `http`/`https` sin credenciales.
- `GET /health` → `{ "status": "ok" }`.

Errores: timeout configurable y cancelación. Se distinguen timeout, red, servidor, respuesta no válida y cancelado. El README del backend no documenta el formato de errores; si la respuesta trae `detail` como texto (formato estándar de FastAPI) se muestra ese mensaje y, si no, uno genérico con el código HTTP.

## Requisitos

- Node.js 20 o superior (probado con Node 24.21.0 y npm 11.19.0).
- npm.

## Instalación y arranque

```bash
npm install
cp .env.example .env     # opcional: ajusta la configuración
npm run dev              # http://localhost:3000
```

Otros comandos:

```bash
npm run typecheck        # comprobación de tipos con vue-tsc
npm test                 # pruebas del cliente de la API (no requiere backend)
npm run build            # compilación de producción
npm run preview          # sirve la compilación de producción
```

### Modo demostración y modo real

- **Durante la sesión:** el interruptor "Modo demo" del panel de conversación cambia entre ambos modos.
- **Al arrancar:** `NUXT_PUBLIC_DEMO_MODE` fija el estado inicial.

Para trabajar con el backend real:

```bash
# 1. Arrancar FastAPI (rama backend-fastapi, carpeta backend)
uvicorn main:app --reload          # http://127.0.0.1:8000

# 2. Arrancar el frontend en modo real
NUXT_PUBLIC_DEMO_MODE=false npm run dev
```

O bien, en `.env`: `NUXT_PUBLIC_DEMO_MODE=false`. En modo real, el pie del chat indica "Conectado a FastAPI" o "Servidor FastAPI no disponible".

## Variables de entorno

Se definen en `.env` (ver `.env.example`) y se exponen al cliente mediante `runtimeConfig.public`.

| Variable | Valor por defecto | Descripción |
| --- | --- | --- |
| `NUXT_PUBLIC_API_BASE` | `http://127.0.0.1:8000` | URL base del backend FastAPI |
| `NUXT_PUBLIC_API_TIMEOUT_MS` | `60000` | Tiempo máximo de espera de la petición, en milisegundos |
| `NUXT_PUBLIC_DEMO_MODE` | `true` | Estado inicial del modo demostración |

Las variables `NUXT_PUBLIC_*` son visibles en el navegador: no guardes en ellas claves ni secretos.

## Estado de verificación

### Verificado automáticamente

- `npm run typecheck` termina sin errores.
- `npm run build` termina correctamente.
- `npm test`: 19 de 19 pruebas superadas. Usan un servidor HTTP local que imita el contrato documentado (no el backend real) y cubren:
  - envío `POST /api/ask` con `multipart/form-data`, campo `audio` y extensión admitida;
  - interpretación del ejemplo de respuesta del README, visemas y `audio_url` relativa;
  - validación de URLs de `open_url` y de audio (esquemas peligrosos, credenciales, otros orígenes);
  - errores HTTP con y sin `detail`, JSON no válido, timeout, cancelación y servidor apagado;
  - `GET /health`.

### Pendiente de verificar con el backend real

- Que FastAPI acepta la grabación de cada navegador (`webm` desde Chrome/Firefox, `m4a` desde Safari).
- Respuesta real de `/api/ask`, incluidos `visemes` y `action`.
- Que `audio_url` se sirve desde el mismo origen que la API y se reproduce.
- Formato real de los errores.
- CORS para el origen del frontend (`http://localhost:3000`).

### Pendiente de verificar manualmente en navegador

- Permisos del micrófono (concedido, denegado, sin micrófono) y límite de 60 s.
- Grabación y desbloqueo de audio en Safari (macOS e iOS).
- Apertura de `open_url` y botón alternativo si se bloquea la ventana emergente.
- Lectores de pantalla (VoiceOver).

El modo demostración no ejercita ninguna de las partes que dependen del backend.

## Limitaciones conocidas

- El avatar 3D tiene su contenedor y sus datos preparados, pero el componente todavía no está integrado.
- `tests/donnaApi.test.ts` se ejecuta con Node (que elimina los tipos), pero no entra en `npm run typecheck`; el código que prueba sí.
- El navegador solo concede el micrófono en `localhost` o HTTPS.

## Seguridad de dependencias

`npm audit` (y `npm audit --omit=dev`) informa de 14 vulnerabilidades (7 críticas y 7 altas), todas en dependencias transitivas de `nuxt`. Proceden de tres paquetes; el resto de avisos (`nuxt`, `@nuxt/devtools`, `nitropack`, `listhen`, `globby`, `fast-glob`, `micromatch`…) aparecen solo por depender de ellos.

| Paquete | Gravedad | Usado por | Ámbito | Versión corregida |
| --- | --- | --- | --- | --- |
| `simple-git` 3.36.0 / `@simple-git/argv-parser` 1.1.1 | Crítica | `@nuxt/devtools` | Solo desarrollo | 4.0.2, incompatible con `@nuxt/devtools` 3.x |
| `node-forge` 1.4.0 | Alta | `listhen` (CLI de desarrollo de Nitro) | Solo desarrollo | No publicada |
| `braces` 3.0.3 | Alta | `globby` → `nitropack` | Solo compilación | No publicada |

**Riesgo real**

- Ninguno de estos paquetes se incluye en la compilación de producción (`.output`) ni se ejecuta en el navegador.
- `simple-git`: DevTools solo ejecuta `git branch`, `git rev-parse` y `git status` con argumentos fijos. Además, **DevTools está desactivado** en `nuxt.config.ts`, así que el módulo no se carga ni siquiera en desarrollo.
- `node-forge`: el aviso afecta a la verificación de firmas RSA; `listhen` solo lo usa para generar certificados HTTPS locales.
- `braces`: denegación de servicio con patrones glob muy anidados; los patrones los define la configuración de Nitro, no el usuario.

**Por qué no se han forzado actualizaciones**

- `npm audit fix --force` rebajaría Nuxt a 3.7.4.
- `simple-git` 4.x eliminó la exportación por defecto que importa `@nuxt/devtools` 3.4.2, de modo que forzarla con `overrides` rompería el entorno de desarrollo.
- `@nuxt/devtools` 4 solo existe en beta y Nuxt 4.6.0 (última estable) exige `^3.4.2`.

Se revisará de nuevo cuando Nuxt publique una versión que incorpore las correcciones. Para usar DevTools puntualmente en local, basta con poner `devtools: { enabled: true }` en `nuxt.config.ts`, sin publicar ese cambio.
