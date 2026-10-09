import sqlite3
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS interaccion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_hora TEXT NOT NULL,
    idioma TEXT NOT NULL,
    pregunta TEXT NOT NULL,
    respuesta TEXT NOT NULL,
    comando_id INTEGER,
    archivo_audio TEXT,
    t_transcripcion_ms INTEGER,
    t_sintesis_ms INTEGER,
    t_total_ms INTEGER NOT NULL,
    estado TEXT NOT NULL,
    mensaje_error TEXT
)
"""


class History:
    """Stores every interaction in a local SQLite database."""

    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self._execute(SCHEMA)

    def _execute(self, sql, params=()):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    def add(self, question, answer, audio_file, t_stt_ms, t_tts_ms, t_total_ms,
            language="es", status="ok", error=None):
        self._execute(
            "INSERT INTO interaccion (fecha_hora, idioma, pregunta, respuesta, "
            "archivo_audio, t_transcripcion_ms, t_sintesis_ms, t_total_ms, "
            "estado, mensaje_error) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), language, question,
             answer, audio_file, t_stt_ms, t_tts_ms, t_total_ms, status, error),
        )

    def latest(self, limit=20):
        rows = self._execute(
            "SELECT * FROM interaccion ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in rows]