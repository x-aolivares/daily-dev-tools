"""Helpers de git para no repetir subprocess en cada comando."""
from __future__ import annotations

import subprocess


def git(*args: str) -> int:
    """Corre git con la salida pegada a la terminal. Devuelve el exit code."""
    return subprocess.run(["git", *args]).returncode


def must(rc: int) -> None:
    """Corta acá si el paso anterior falló (ej: fetch sin red)."""
    if rc:
        raise SystemExit(rc)


def capture(*args: str) -> str:
    """Corre git/devuelve stdout limpio. Lanza si falla."""
    out = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def current_branch() -> str:
    return capture("rev-parse", "--abbrev-ref", "HEAD")


def repo_root() -> str:
    return capture("rev-parse", "--show-toplevel")
