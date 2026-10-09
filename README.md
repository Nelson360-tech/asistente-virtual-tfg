# Donna: asistente virtual por voz con avatar

Trabajo Final de Bàtxelor en Informática. Donna es un asistente virtual que recibe preguntas habladas, las interpreta y responde con voz, acompañado de un avatar 3D cuya boca se sincroniza con la respuesta mediante visemas.

Todo el procesamiento de voz se ejecuta en el propio ordenador: el audio del usuario no se envía a servicios externos.

## Arquitectura

```
Navegador: frontend Nuxt + avatar 3D (Three.js)
        │  audio de la pregunta (POST /api/ask)
        ▼
Backend FastAPI
  ├─ SpeechToText  → transcribe el audio (faster-whisper, local)
  ├─ Commands      → decide la respuesta y una acción opcional
  ├─ TextToSpeech  → genera la voz y los tiempos de cada fonema (Piper, local)
  ├─ LipSync       → convierte fonemas en visemas con marca temporal (OpenFaceFX)
  └─ History       → guarda cada interacción y sus tiempos (SQLite)
        │  texto + audio + visemas
        ▼
Navegador reproduce el audio y anima la boca del avatar
```

## Requisitos

- Python 3.11 o superior (probado con 3.13 en Windows 11)
- Node.js 20 o superior (probado con 24) para el frontend
- Git
- Unos 500 MB libres para los modelos de voz y reconocimiento

## Instalación del backend

Desde la raíz del repositorio, en Windows (Command Prompt):

```
cd backend
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
python -m piper.download_voices es_AR-daniela-high --download-dir voices
```

En macOS o Linux, la activación del entorno es `source .venv/bin/activate`.

La primera vez que arranca el servidor se descarga automáticamente el modelo de reconocimiento de voz, por lo que tarda un poco más.

## Instalación del frontend

Desde la raíz del repositorio:

```
cd frontend
npm install
copy .env.example .env
```

En el archivo `.env`, poner `NUXT_PUBLIC_DEMO_MODE=false` para usar el backend real. En macOS o Linux, usar `cp` en lugar de `copy`.

## Ejecución

Se necesitan dos terminales.

Terminal 1, backend:

```
cd backend
.venv\Scripts\activate.bat
uvicorn main:app --reload
```

Terminal 2, frontend:

```
cd frontend
npm run dev
```

- Aplicación: `http://localhost:3000`
- API: `http://127.0.0.1:8000`
- Documentación interactiva para probar el endpoint: `http://127.0.0.1:8000/docs`

Antes de arrancar el backend conviene comprobar que el puerto 8000 está libre (`netstat -ano | findstr :8000` en Windows).

## API

### `POST /api/ask`

Recibe un archivo de audio en un campo de formulario llamado `audio` (webm, m4a, mp3 o wav).

Respuesta:

```json
{
  "question": "¿Qué hora es?",
  "answer": "Son las 18 horas con 19 minutos",
  "audio_url": "/audio/a5544a8c....wav",
  "visemes": [
    {"start": 0.0, "end": 0.133, "viseme": "sil"},
    {"start": 0.133, "end": 0.167, "viseme": "O"}
  ],
  "action": null
}
```

| Campo | Descripción |
|---|---|
| `question` | Transcripción de lo que dijo el usuario |
| `answer` | Respuesta en texto |
| `audio_url` | Ruta del audio de la respuesta, relativa al servidor |
| `visemes` | Posiciones de boca con inicio y fin en segundos desde el comienzo del audio |
| `action` | `null`, o una acción para el cliente, por ejemplo `{"type": "open_url", "url": "..."}` |

Los visemas siguen el estándar de 15 posiciones de Oculus: `sil`, `PP`, `FF`, `TH`, `DD`, `kk`, `CH`, `SS`, `nn`, `RR`, `aa`, `E`, `I`, `O`, `U`.

### `GET /api/history?limit=20`

Devuelve las últimas interacciones registradas (por defecto 20), con la pregunta, la respuesta, el archivo de audio y el tiempo de cada fase en milisegundos (`t_transcripcion_ms`, `t_sintesis_ms`, `t_total_ms`).

### `GET /health`

Comprueba que el servidor está en marcha. Devuelve `{"status": "ok"}`.

## Comandos disponibles

| Frase | Respuesta |
|---|---|
| "¿Qué hora es?" | Dice la hora actual |
| "¿Qué día es?" | Dice el día de la semana |
| "Abrir YouTube" | Responde y devuelve la acción de abrir YouTube |

Cualquier otra frase recibe una respuesta indicando que no se entendió el pedido.

## Estructura

```
backend/
  main.py               Aplicación FastAPI y endpoints
  benchmark.py          Medición del rendimiento de los modelos de voz
  requirements.txt      Dependencias con versiones fijadas
  donna/
    speech_to_text.py   Voz a texto
    commands.py         Interpretación de comandos
    text_to_speech.py   Texto a voz y tiempos de fonemas
    lip_sync.py         Generación de visemas
    history.py          Historial de interacciones en SQLite
  voices/               Voz de Piper (no se sube al repositorio)
  audio/                Audios generados (no se sube al repositorio)
  donna.db              Base de datos del historial (no se sube al repositorio)
frontend/
  app/app.vue                       Interfaz: grabación, conversación y avatar
  app/components/DonnaAvatar.client.vue   Avatar 3D con sincronización labial
  app/utils/visemeMouth.ts          Traducción de visemas a expresiones faciales
  app/services/donnaApi.ts          Cliente de la API
  public/models/facecap.glb         Modelo 3D del avatar
  tests/                            Pruebas (npm test)
docs/diagramas/         Diagramas UML y figuras de la memoria
```

Los archivos de la raíz (`asistente.py`, `audio_input.py`, `audio_output.py`, `comandos.py`, `main.py`) corresponden a la primera versión de consola del asistente y se conservan como referencia.

## Tecnologías

| Componente | Tecnología | Motivo |
|---|---|---|
| Servidor | FastAPI | Ligero, con documentación interactiva automática |
| Voz a texto | faster-whisper | Funciona sin Internet y no envía el audio a terceros |
| Texto a voz | Piper | Voz natural, local, con voz en español de Argentina |
| Visemas | OpenFaceFX | Convierte los tiempos de fonemas de Piper en visemas |
| Historial | SQLite | Incluido en Python, sin servidor de base de datos |
| Frontend | Nuxt 4, Vue 3 y TypeScript | Estructura en componentes y tipado del contrato con la API |
| Avatar | Three.js | Renderizado 3D en el navegador y animación de las expresiones faciales |

## Notas técnicas

- `av` está fijado en la versión 18.1.0: la versión 19 eliminó una opción que utiliza faster-whisper.
- La respuesta de Piper se genera por frases; los audios y los tiempos de los fonemas se concatenan en orden, de modo que los visemas quedan sincronizados con el audio completo.
- CORS está abierto a cualquier origen para facilitar el desarrollo. En producción debe limitarse a la dirección del frontend.
- El avatar usa el modelo `facecap.glb` de los ejemplos de Three.js, con 52 expresiones faciales ARKit. Los visemas se traducen a esas expresiones en `visemeMouth.ts`, y la boca se sincroniza con el instante actual del audio (`currentTime`).
- `nuxt.config.ts` incluye una configuración alternativa para un fallo de Nuxt 4.6.0 en Windows ([nuxt/nuxt#36467](https://github.com/nuxt/nuxt/issues/36467)), que devolvía un error 500 en todas las páginas.

## Medir el rendimiento

```
cd backend
python benchmark.py "ruta\a\una\grabacion.m4a"
```

Mide el reconocimiento de voz y la síntesis con cinco repeticiones (media y desviación). Sin argumento, solo mide la síntesis. Para comparar voces, descargar también `es_MX-ald-medium` en `voices/`. Conviene medir con el equipo conectado a la corriente: el modo de ahorro de energía multiplica los tiempos.
