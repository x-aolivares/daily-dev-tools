"""Shortcuts de git.

Para crear uno nuevo:  ddt new <nombre>   (crea el archivo)
                       ddt-reload        (aparece como alias corto)
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from ..registry import shell_command

# .env del repo cuando está instalado en modo editable; si no existe,
# cae al WORKSPACE_PATH del entorno.
_REPO_ROOT = Path(__file__).resolve().parents[3]


@shell_command("gtws", "go to al workspace")
def go_to_workspace() -> str:
    load_dotenv(_REPO_ROOT / ".env")
    path = os.getenv("WORKSPACE_PATH")
    if not path:
        return 'cd "${WORKSPACE_PATH:?WORKSPACE_PATH no está definido}"'
    return f'cd "{path}"'
