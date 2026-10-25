"""setup / reload / teardown.

Convención: el stdout de estos comandos es CÓDIGO shell (lo consume
`eval "$(ddt setup)"`), y toda salida humana va a stderr. Mezclarlos rompe el eval.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from ..config import BASHRC, BASH_PROFILE, SHORTCUTS_FILE, path_entry, shell_path, short
from . import block, generate

SOURCE_BASHRC = '[ -f "$HOME/.bashrc" ] && . "$HOME/.bashrc"'

# gfp() { ... }   /   ddt-reload() {   — lo que declara shortcuts.sh
_FUNC_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*\(\)")


# ---------------------------------------------------------------- setup

def setup() -> int:
    """Instala el bloque en ~/.bashrc y deja la sesión actual al día."""
    generate.generate()
    block.install(BASHRC, _bashrc_lines())
    _ensure_login_shell()

    if not sys.stdout.isatty():
        sys.stdout.write(_session_setup_code())
        return 0

    print(f"instalado: {short(BASHRC)}", file=sys.stderr)
    print(f"           {short(SHORTCUTS_FILE)}", file=sys.stderr)
    print('para usarlo YA en esta terminal:  eval "$(ddt setup)"', file=sys.stderr)
    return 0


def _bashrc_lines() -> list[str]:
    p = path_entry()
    sh = shell_path(SHORTCUTS_FILE)
    return [
        f'case ":$PATH:" in *":{p}:"*) : ;; *) PATH="{p}:$PATH"; export PATH ;; esac',
        f'[ -f "{sh}" ] && . "{sh}"',
    ]


def _ensure_login_shell() -> None:
    """Git Bash arranca como login shell: sin ~/.bash_profile que cargue
    ~/.bashrc, el bloque nunca se ejecuta.

    Se busca el substring `.bashrc` y no el texto exacto: hay varias formas
    válidas de escribirlo (`test -f ~/.bashrc && . ~/.bashrc`,
    `[ -f "$HOME/.bashrc" ] && ...`, `source ~/.bashrc`).
    """
    if not block.has_text(BASH_PROFILE, ".bashrc"):
        block.install(BASH_PROFILE, [SOURCE_BASHRC])


def _session_setup_code() -> str:
    p = path_entry()
    return (
        f'case ":$PATH:" in *":{p}:"*) : ;; *) PATH="{p}:$PATH"; export PATH ;; esac\n'
        f'. "{shell_path(SHORTCUTS_FILE)}"\n'
    )


# --------------------------------------------------------------- reload

def reload() -> int:
    """Regenera shortcuts.sh tras crear o editar un comando."""
    names = generate.generate()
    if not sys.stdout.isatty():
        sys.stdout.write(f'. "{shell_path(SHORTCUTS_FILE)}"\n')
        return 0
    print(f"{len(names)} shortcuts en {short(SHORTCUTS_FILE)}", file=sys.stderr)
    print("recargalos con:  ddt-reload", file=sys.stderr)
    return 0


# ------------------------------------------------------------- teardown

def teardown() -> int:
    """Revierte setup: borra bloques, el archivo generado y las functions."""
    names = _file_shortcuts()
    block.remove(BASHRC)
    block.remove(BASH_PROFILE)
    SHORTCUTS_FILE.unlink(missing_ok=True)

    if not sys.stdout.isatty():
        sys.stdout.write(_session_teardown_code(names))
        return 0

    print(f"eliminado de {short(BASHRC)} y {short(BASH_PROFILE)}", file=sys.stderr)
    print('para limpiar esta terminal:  eval "$(ddt teardown)"', file=sys.stderr)
    print("y después:  pip uninstall daily-dev-tools", file=sys.stderr)
    return 0


def _file_shortcuts() -> list[str]:
    """Qué functions declara el shortcuts.sh actual.

    Se lee el archivo y no el registro: pueden quedar aliases de versiones
    viejas que hay que limpiar igual.
    """
    if not SHORTCUTS_FILE.exists():
        return []
    names = []
    with SHORTCUTS_FILE.open("r", encoding="utf-8", newline="") as fh:
        for line in fh:
            m = _FUNC_RE.match(line)
            if m:
                names.append(m.group(1))
    return sorted(set(names))


def _session_teardown_code(names: list[str]) -> str:
    """Borra el entry del PATH en formato de la shell (no en formato Windows):
    dentro de Git Bash el PATH es `:` y los paths son /c/..., así que hay que
    hacerlo con bash y no con os.pathsep."""
    p = path_entry()
    lines = [
        "_ddt_rm() {",
        '  local out="" seg',
        "  local IFS=:",
        "  for seg in $PATH; do",
        f'    [ "$seg" = "{p}" ] && continue',
        '    out="${out:+$out:}$seg"',
        "  done",
        '  PATH="$out"',
        "  export PATH",
        "}",
        "_ddt_rm",
        "unset -f _ddt_rm",
    ]
    if names:
        lines.append(f"unset -f {' '.join(names)} 2>/dev/null || true")
    return "\n".join(lines) + "\n"
