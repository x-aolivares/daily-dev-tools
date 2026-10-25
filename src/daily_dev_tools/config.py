"""Rutas del paquete y de la config del usuario."""
from __future__ import annotations

import os
import shutil
import sys
import sysconfig
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
COMMANDS_DIR = PACKAGE_DIR / "commands"

CONFIG_DIR = Path.home() / ".config" / "ddt"
SHORTCUTS_FILE = CONFIG_DIR / "shortcuts.sh"

BASHRC = Path.home() / ".bashrc"
BASH_PROFILE = Path.home() / ".bash_profile"


def scripts_dir() -> Path:
    """Directorio donde pip dejó el binario `ddt`.

    No es el padre de sys.executable: en Windows el instalador pone python.exe
    en la raíz y los binarios en `Scripts/`, y pip a veces instala en el user
    site (`AppData/Roaming/...`) en vez del Python del sistema. Por eso se
    busca el binario de verdad entre todos los schemes de pip.
    """
    for candidate in _candidates():
        if _has_ddt(candidate):
            return candidate
    return Path(sysconfig.get_path("scripts"))


def _has_ddt(directory: Path) -> bool:
    return (directory / "ddt.exe").exists() or (directory / "ddt").exists()


def _candidates() -> list[Path]:
    found: list[Path] = []
    if which := shutil.which("ddt"):
        found.append(Path(which).parent)

    schemes = sysconfig.get_scheme_names()
    ordered = sorted(schemes, key=lambda s: (s != sysconfig.get_default_scheme(),
                                             not s.endswith("_user")))
    for scheme in ordered:
        try:
            found.append(Path(sysconfig.get_path("scripts", scheme=scheme)))
        except (KeyError, ValueError):
            pass

    if len(sys.argv) > 1 and sys.argv[0] not in ("", "-c"):
        arg0 = Path(sys.argv[0]).resolve()
        if arg0.name.startswith("ddt"):
            found.append(arg0.parent)

    found.append(Path(sys.executable).resolve().parent / "Scripts")

    unique: list[Path] = []
    for path in found:
        if path not in unique:
            unique.append(path)
    return unique


def shell_path(path: Path) -> str:
    """Ruta en formato de la shell.

    En Windows hay que usar `/c/Users/...` y nunca `C:/Users/...`: el `:` del
    disco se confunde con el separador de PATH (MSYS convierte el PATH de
    Windows a POSIX al arrancar, y nosotros hacemos lo mismo acá).
    """
    s = str(path)
    if os.name == "nt":
        s = s.replace("\\", "/")
        if len(s) >= 2 and s[1] == ":":
            s = f"/{s[0].lower()}{s[2:]}"
    return s


def path_entry() -> str:
    """El Scripts/ del intérprete, listo para meter en el PATH de la shell."""
    return shell_path(scripts_dir())


def short(path: Path) -> str:
    """Ruta abreviada para mostrar en mensajes."""
    try:
        return str(path).replace(str(Path.home()), "~").replace("\\", "/")
    except ValueError:
        return str(path)
