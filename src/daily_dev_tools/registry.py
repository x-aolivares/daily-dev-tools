"""Registro central: un comando = un bloque con @command (o shell()).

De acá sale todo lo demás: el parser de `ddt`, la lista de comandos y el
archivo de aliases que se genera para la shell. Agregar un comando nuevo es
escribir un bloque en commands/ y correr `ddt-reload`.
"""
from __future__ import annotations

import argparse
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass

Run = Callable[[argparse.Namespace], int]
AddArgs = Callable[[argparse.ArgumentParser], None]

# Un nombre de comando tiene que servir también como nombre de function en bash.
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


@dataclass(frozen=True)
class Command:
    name: str
    help: str
    run: Run | None = None    # lógica en Python -> se invoca como `ddt <name>`
    bash: str | None = None   # lógica en bash   -> solo alias (cd, export, source)
    args: Sequence[AddArgs] = ()
    shortcut: bool = True     # ¿genera también el alias corto `name`?

    @property
    def is_shell(self) -> bool:
        return self.run is None


COMMANDS: dict[str, Command] = {}


def command(
    name: str,
    help: str,
    *,
    shortcut: bool = True,
    args: Sequence[AddArgs] = (),
) -> Callable[[Run], Run]:
    """Registra un comando con lógica en Python."""

    def decorator(run: Run) -> Run:
        _register(Command(name=name, help=help, run=run, args=args, shortcut=shortcut))
        return run

    return decorator


def shell(name: str, help: str, *, bash: str) -> Command:
    """Registra un comando cuya lógica vive en la shell.

    Usalo para lo que no puede salir de la shell: cd, export, source, eval.
    Se usa como llamada, no como decorador:

        shell("groot", "cd a la raíz", bash='cd "$(git rev-parse --show-toplevel)"')
    """
    return _register(Command(name=name, help=help, bash=bash))


def shell_command(name: str, help: str, *, args: Sequence[Callable[[argparse.ArgumentParser], None]] = ()) -> Callable:
    """Decorador para comandos shell.

    Modo estático (sin args y función sin parámetros): la función se ejecuta al
    importar y debe devolver el bash a registrar (compatibilidad hacia atrás).

    Modo híbrido (con args o función con parámetro): la función recibe el
    Namespace parseado y debe devolver el bash a ejecutar; se registra un
    comando Python que imprime ese bash y un alias de shell que hace
    `eval "$(ddt name "$@")"`, permitiendo flags/args y efecto en la shell
    padre (cd, export, source).
    """

    def decorator(fn: Callable) -> Command:
        import inspect

        param_count = len(inspect.signature(fn).parameters)

        # Modo estático (compatibilidad hacia atrás).
        if not args and param_count == 0:
            bash = fn()
            if not isinstance(bash, str) or not bash.strip():
                raise ValueError(f"{name!r}: la función debe devolver un bash no vacío")
            return shell(name, help, bash=bash)

        # Modo híbrido.
        def _run(parsed: argparse.Namespace) -> int:
            if param_count == 0:
                result = fn()
            else:
                class _ShellArgs(argparse.Namespace):
                    def __bool__(self) -> bool:
                        return any(bool(v) for v in vars(self).values())

                filtered = {k: v for k, v in vars(parsed).items() if k not in ("command", "func")}
                result = fn(_ShellArgs(**filtered))

            if not isinstance(result, str) or not result.strip():
                raise ValueError(f"{name!r}: la función debe devolver un bash no vacío")
            print(result)
            return 0

        bash_alias = f'eval "$(ddt {name} "$@")"'
        cmd = Command(name=name, help=help, run=_run, bash=bash_alias, args=list(args), shortcut=True)
        return _register(cmd)

    return decorator


def _register(cmd: Command) -> Command:
    if not NAME_RE.match(cmd.name):
        raise ValueError(f"nombre de comando inválido: {cmd.name!r}")
    if cmd.name in COMMANDS:
        raise ValueError(f"comando duplicado: {cmd.name!r}")
    if cmd.run is None and cmd.bash is None:
        raise ValueError(f"{cmd.name!r}: necesita run (Python) o bash")
    COMMANDS[cmd.name] = cmd
    return cmd
