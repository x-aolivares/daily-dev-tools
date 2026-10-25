"""Atajos cuya lógica vive en la shell.

Para lo que no puede salir de una shell: cd, export, source, eval. Si lo
mandás por Python (un proceso hijo), no le puede cambiar el entorno a la
terminal que lo invocó.
"""
from __future__ import annotations

from ..registry import shell

shell(
    "groot",
    "cd a la raíz del repo",
    bash='cd "$(git rev-parse --show-toplevel)"',
)

shell(
    "ggl",
    "git log con diff de archivos",
    bash='git log --stat --oneline -n "${1:-10}"',
)
