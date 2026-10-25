"""Bloque idempotente con marcadores, para tocar ~/.bashrc sin romper nada.

El bloque se inserta con un `\n` adelante y otro atrás, y al quitarlo se
retiran exactamente esos dos: así `teardown` deja el archivo byte a byte como
estaba.
"""
from __future__ import annotations

from pathlib import Path

OPEN = "# >>> ddt >>>"
CLOSE = "# <<< ddt <<<"


def install(path: Path, lines: list[str]) -> None:
    """Escribe (o reemplaza) el bloque dentro de `path`. Idempotente."""
    text = remove_block(_read(path))
    if text and not text.endswith(("\n", "\r")):
        text += "\n"                       # normalización única

    body = "\n".join([OPEN, *lines, CLOSE])
    prefix = "\n" if text else ""          # línea en blanco antes del bloque
    _write(path, f"{text}{prefix}{body}\n")


def remove(path: Path) -> bool:
    """Borra el bloque. Devuelve True si había algo que borrar."""
    text = _read(path)
    if OPEN not in text:
        return False
    _write(path, remove_block(text))
    return True


def installed(path: Path) -> bool:
    return OPEN in _read(path)


def has_text(path: Path, text: str) -> bool:
    return text in _read(path)


def remove_block(text: str) -> str:
    """Quita el bloque y los dos `\n` que `install` agregó alrededor."""
    while OPEN in text:
        start = text.index(OPEN)
        end = text.index(CLOSE, start) + len(CLOSE)
        before = "\n" if start and text[start - 1] == "\n" else ""
        after = "\n" if text[end : end + 1] == "\n" else ""
        text = text[: start - len(before)] + text[end + len(after) :]
    return text


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    with path.open("r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(text)
