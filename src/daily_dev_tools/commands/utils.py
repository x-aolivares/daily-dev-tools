"""Shortcuts de git.

Para crear uno nuevo:  ddt new <nombre>   (crea el archivo)
                       ddt-reload        (aparece como alias corto)
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from ..params import path, setup
from ..registry import shell_command

# .env del repo cuando está instalado en modo editable; si no existe,
# cae al WORKSPACE_PATH del entorno.
_REPO_ROOT = Path(__file__).resolve().parents[3]


@shell_command("gtws", "go to al workspace", args=[path])
def go_to_workspace(args) -> str:
    if not args:
        load_dotenv(_REPO_ROOT / ".env")
        workspace = os.getenv("WORKSPACE_PATH")
    else:
        workspace = args.path

    if not workspace:
        return 'cd "${WORKSPACE_PATH:?WORKSPACE_PATH no está definido}"'

    return f'cd "{workspace}"'


@shell_command("gth", "go to project home", args=[])
def go_to_workspace(args) -> str:
    vr = Path(__file__).resolve().parent.parent.parent.parent.as_posix()
    return f"cd {vr}"


@shell_command("rt", "reload terminal", args=[setup])
def go_to_workspace(args) -> str:
    if not args.setup or args.setup != "setup":
        return f"source ~/.bashrc"

    return 'ddt setup && eval "$(ddt setup)"'