"""Comandos de administración: existen, pero no generan alias corto."""
from __future__ import annotations

import shutil
import sys
from importlib.metadata import version

from ..config import BASHRC, BASH_PROFILE, SHORTCUTS_FILE, scripts_dir, shell_path, short
from ..registry import COMMANDS, command
from ..scaffold import new as scaffold_new
from ..shell import block, reload as reload_shell, setup as setup_shell, teardown as teardown_shell


# ----------------------------------------------------------- argumentos

def name_arg(p) -> None:
    p.add_argument("name", help="nombre del comando (ej: gdeploy)")


def all_arg(p) -> None:
    p.add_argument("--all", action="store_true", help="incluye los comandos de ddt")


# ------------------------------------------------------------ comandos

@command("setup", "Instala la integración con Git Bash", shortcut=False)
def setup_cmd(a) -> int:
    return setup_shell()


@command("reload", "Regenera los aliases tras crear/editar un comando", shortcut=False)
def reload_cmd(a) -> int:
    return reload_shell()


@command("teardown", "Deshace setup (bloques, archivo y aliases)", shortcut=False)
def teardown_cmd(a) -> int:
    return teardown_shell()


@command("new", "Crea un comando nuevo", shortcut=False, args=[name_arg])
def new_cmd(a) -> int:
    print(scaffold_new(a.name))
    return 0


@command("list", "Lista los shortcuts disponibles", shortcut=False, args=[all_arg])
def list_cmd(a) -> int:
    cmds = sorted(COMMANDS.values(), key=lambda c: c.name)
    if not a.all:
        cmds = [c for c in cmds if c.shortcut]
    if not cmds:
        print("no hay shortcuts todavía. Creá uno con:  ddt new <nombre>")
        return 0

    width = max(len(c.name) for c in cmds)
    for c in cmds:
        kind = "shell" if c.is_shell else ("alias" if c.shortcut else "ddt")
        print(f"  {c.name.ljust(width)}  {kind:5}  {c.help}")
    print(f"\n  {len(cmds)} comando(s)  ·  aliases en {short(SHORTCUTS_FILE)}")
    return 0


@command("version", "Versión instalada", shortcut=False)
def version_cmd(a) -> int:
    print(f"ddt {version('daily_dev_tools')}")
    print(f"python {sys.version.split()[0]}")
    binary = scripts_dir() / ("ddt.exe" if sys.platform == "win32" else "ddt")
    print(f"binario {short(binary)}")
    return 0


@command("doctor", "Diagnóstico de la instalación", shortcut=False)
def doctor_cmd(a) -> int:
    problems = 0

    def check(ok: bool, label: str, fix: str = "") -> None:
        nonlocal problems
        print(f"  {'OK   ' if ok else 'FALLO'} {label}")
        if not ok:
            problems += 1
            if fix:
                print(f"         -> {fix}")

    check(shutil.which("git") is not None, "git en el PATH", "instalá git")
    check(sys.version_info >= (3, 10), f"python {sys.version.split()[0]} (>= 3.10)")

    binary = scripts_dir() / ("ddt.exe" if sys.platform == "win32" else "ddt")
    check(binary.exists(), f"binario {short(binary)}", "pip install -e .")
    if shutil.which("ddt") is None:
        print("  aviso  no está en el PATH de Windows; en Git Bash sí lo está")
        print(f"         (el bloque agrega {shell_path(scripts_dir())})")
    check(block.installed(BASHRC), f"bloque en {short(BASHRC)}", "ddt setup")

    profile_ok = block.has_text(BASH_PROFILE, ".bashrc")
    check(profile_ok, f"{short(BASH_PROFILE)} carga .bashrc", "ddt setup")
    check(SHORTCUTS_FILE.exists(), f"generado: {short(SHORTCUTS_FILE)}", "ddt setup")

    if problems:
        print(f'\n{problems} problema(s). Onboarding:  eval "$(ddt setup)"')
        return 1
    print("\ntodo bien.")
    return 0
