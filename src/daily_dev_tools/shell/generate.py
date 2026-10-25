"""Genera ~/.config/ddt/shortcuts.sh — 100% derivado, nunca se edita a mano."""
from __future__ import annotations

from ..config import CONFIG_DIR, SHORTCUTS_FILE, shell_path
from ..registry import COMMANDS

HEADER = """\
# generado por daily-dev-tools - no editar a mano
# regenerar con:  ddt-reload   (o  ddt reload && . ~/.config/ddt/shortcuts.sh)
"""

RELOAD_FN = f"""
ddt-reload() {{
  ddt reload || return $?
  . "{shell_path(SHORTCUTS_FILE)}"
  echo "shortcuts recargados"
}}
"""


def generate() -> list[str]:
    """Escribe shortcuts.sh y devuelve los nombres de las functions creadas."""
    names: list[str] = []
    lines = [HEADER]

    for name in sorted(COMMANDS):
        cmd = COMMANDS[name]
        if not cmd.shortcut:
            continue
        names.append(name)
        if cmd.bash:
            lines.append(f"{name}() {{ {cmd.bash} ; }}")
        else:
            lines.append(f'{name}() {{ ddt {name} "$@" ; }}')

    lines.append(RELOAD_FN)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # newline="\n": bash no banca CRLF (Git for Windows lo tolera a medias,
    # pero `eval "$(ddt reload)"` se rompe con el \r adentro de la ruta)
    with SHORTCUTS_FILE.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    return names
