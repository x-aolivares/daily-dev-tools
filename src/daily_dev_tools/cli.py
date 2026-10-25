"""ddt <comando> [args] — arma el parser desde lo que registró @command."""
from __future__ import annotations

import argparse
import sys

from . import __version__
from . import commands  # noqa: F401  importar el paquete = registrar todo
from .registry import COMMANDS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ddt",
        description="Shortcuts del día a día. Los alias cortos (gfp, gcp...) "
                    "viven en shortcuts.sh; esto es el dispatcher.",
    )
    p.add_argument("--version", action="version", version=f"ddt {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    for cmd in sorted(COMMANDS.values(), key=lambda c: c.name):
        sp = sub.add_parser(cmd.name, help=cmd.help, description=cmd.help)
        for add_args in cmd.args:
            add_args(sp)
        sp.set_defaults(func=cmd.run)

    return p


def main(argv: list[str] | None = None) -> int:
    _utf8(sys.stdout)
    _utf8(sys.stderr)
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as e:
        return _exit_code(e)          # argparse ya imprimió help/usage

    if args.func is None:             # comando que solo vive en la shell
        cmd = COMMANDS[args.command]
        print(f"ddt: {cmd.name} es un shortcut de shell, usalo directo:  {cmd.name}",
              file=sys.stderr)
        print(f"      su lógica es: {cmd.bash}", file=sys.stderr)
        return 2

    try:
        return args.func(args) or 0
    except SystemExit as e:           # must() o error de uso nuestro
        return _exit_code(e)
    except KeyboardInterrupt:
        return 130


def _utf8(stream) -> None:
    """Salida en UTF-8 y con fin de línea LF: en Windows la consola usa otra
    codepage (caracteres rotos) y el fin de línea CRLF rompe el
    `eval "$(ddt ...)"`, que le pasa el `\r` adentro de la ruta."""
    try:
        stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    except (AttributeError, ValueError):
        pass


def _exit_code(e: SystemExit) -> int:
    """SystemExit(str) = mensaje nuestro; SystemExit(int) = código de git/argparse."""
    if isinstance(e.code, str):
        print(f"ddt: {e.code}", file=sys.stderr)
        return 1
    return int(e.code or 0)


if __name__ == "__main__":
    sys.exit(main())
