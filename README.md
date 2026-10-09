# Donna: asistente virtual por voz con avatar

Trabajo Final de Bàtxelor en Informática. Donna es un asistente virtual que recibe preguntas habladas, las interpreta y responde con voz, acompañado de un avatar 3D cuya boca se sincroniza con la respuesta mediante visemas.

Todo el procesamiento de voz se ejecuta en el propio ordenador: el audio del usuario no se envía a servicios externos.

## Arquitectura

```
Navegador (frontend + avatar)
        │  audio de la pregunta (POST /api/ask)
        ▼
Backend FastAPI
  ├─ SpeechToText  → transcribe el audio (faster-whisper, local)
  ├─ Commands      → decide la respuesta y una acción opcional
  ├─ TextToSpeech  → genera la voz y los tiempos de cada fonema (Piper, local)
  └─ LipSync       → convierte fonemas en visemas con marca temporal (OpenFaceFX)
        │  texto + audio + visemas
        ▼
Navegador reproduce el audio y anima la boca del avatar
```

## Requisitos

- Python 3.11 o superior (probado con 3.13 en Windows 11)
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

## Ejecución

```
cd backend
.venv\Scripts\activate.bat
uvicorn main:app --reload
```

- API: `http://127.0.0.1:8000`
- Documentación interactiva para probar el endpoint: `http://127.0.0.1:8000/docs`

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
  requirements.txt      Dependencias con versiones fijadas
  donna/
    speech_to_text.py   Voz a texto
    commands.py         Interpretación de comandos
    text_to_speech.py   Texto a voz y tiempos de fonemas
    lip_sync.py         Generación de visemas
  voices/               Voz de Piper (no se sube al repositorio)
  audio/                Audios generados (no se sube al repositorio)
```

Los archivos de la raíz (`asistente.py`, `audio_input.py`, `audio_output.py`, `comandos.py`, `main.py`) corresponden a la primera versión de consola del asistente y se conservan como referencia.

## Tecnologías

| Componente | Tecnología | Motivo |
|---|---|---|
| Servidor | FastAPI | Ligero, con documentación interactiva automática |
| Voz a texto | faster-whisper | Funciona sin Internet y no envía el audio a terceros |
| Texto a voz | Piper | Voz natural, local, con voz en español de Argentina |
| Visemas | OpenFaceFX | Convierte los tiempos de fonemas de Piper en visemas |

## Notas técnicas

- `av` está fijado en la versión 18.1.0: la versión 19 eliminó una opción que utiliza faster-whisper.
- La respuesta de Piper se genera por frases; los audios y los tiempos de los fonemas se concatenan en orden, de modo que los visemas quedan sincronizados con el audio completo.
- CORS está abierto a cualquier origen para facilitar el desarrollo. En producción debe limitarse a la dirección del frontend.