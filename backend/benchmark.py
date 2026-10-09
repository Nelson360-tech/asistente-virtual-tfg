"""Experimento controlado de rendimiento de Donna.

Mide, sin servidor y repitiendo cada operación varias veces:
  1. Whisper con beam_size 5 y 1 sobre el mismo audio.
  2. Piper con distintas voces, con y sin tiempos de fonemas.

Uso: python benchmark.py "ruta/al/audio.m4a"
"""
import io
import statistics
import sys
import time
import wave
from pathlib import Path

from piper import PiperVoice

REPS = 5
TEXT = "Son las veintitrés horas con cincuenta y seis minutos"
VOICES_DIR = Path(__file__).parent / "voices"
VOICES = ["es_AR-daniela-high", "es_MX-ald-medium"]


def measure(fn):
    fn()  # primera ejecución de calentamiento, no se cuenta
    times = []
    for _ in range(REPS):
        start = time.perf_counter()
        fn()
        times.append((time.perf_counter() - start) * 1000)
    return statistics.mean(times), statistics.stdev(times)


def report(name, result, extra=""):
    mean, sd = result
    print(f"{name:<42} {mean:8.0f} ms  ± {sd:5.0f} ms  {extra}")


def benchmark_whisper(audio_path):
    from faster_whisper import WhisperModel

    model = WhisperModel("base", device="cpu", compute_type="int8")
    for beam in (5, 1):
        def run():
            segments, _ = model.transcribe(audio_path, language="es", beam_size=beam)
            return " ".join(s.text.strip() for s in segments)

        print(f"  beam_size={beam} transcribe: {run()!r}")
        report(f"Whisper base, beam_size={beam}", measure(run))


def synthesize(voice, alignments):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        voice.synthesize_wav(TEXT, wav, include_alignments=alignments)
    buffer.seek(0)
    with wave.open(buffer, "rb") as wav:
        return wav.getnframes() / wav.getframerate()


def benchmark_piper():
    for name in VOICES:
        path = VOICES_DIR / f"{name}.onnx"
        if not path.exists():
            print(f"  (falta la voz {name}, se omite)")
            continue
        for alignments in (True, False):
            voice = PiperVoice.load(path, include_alignments=alignments)
            seconds = synthesize(voice, alignments)
            result = measure(lambda: synthesize(voice, alignments))
            label = "con fonemas" if alignments else "sin fonemas"
            report(f"Piper {name} {label}", result,
                   f"audio {seconds:.1f} s, factor {result[0] / 1000 / seconds:.2f}")


if __name__ == "__main__":
    print(f"Repeticiones por prueba: {REPS}\n")
    if len(sys.argv) > 1:
        print("Reconocimiento de voz")
        benchmark_whisper(sys.argv[1])
        print()
    print(f"Síntesis de voz: «{TEXT}»")
    benchmark_piper()