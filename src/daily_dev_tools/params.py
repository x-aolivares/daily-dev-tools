"""Argumentos que se repiten entre comandos, definidos una sola vez.

Uso en un comando:

    @command("gfp", "...", args=[branch, checkout])
"""
from __future__ import annotations

import argparse


def branch(p: argparse.ArgumentParser) -> None:
    p.add_argument("branch", nargs="?", help="rama destino (default: la actual)")


def target_branch(p: argparse.ArgumentParser) -> None:
    """Rama obligatoria, pero con el mismo dest=`branch` que `branch`."""
    p.add_argument("branch", help="rama destino")


def create(p: argparse.ArgumentParser) -> None:
    p.add_argument("-b", "--create", action="store_true",
                   help="crea la rama (git checkout -b)")


def checkout(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--checkout",
        action="store_true",
        help="hace checkout de la rama antes de continuar",
    )


def remote(p: argparse.ArgumentParser) -> None:
    p.add_argument("--remote", default="origin", help="remoto (default: origin)")


def commits(p: argparse.ArgumentParser) -> None:
    p.add_argument("commits", nargs="+", help="sha(s) del commit")


def no_pull(p: argparse.ArgumentParser) -> None:
    p.add_argument("--no-pull", action="store_true", help="no hace pull previo")


def limit(p: argparse.ArgumentParser) -> None:
    p.add_argument("-n", type=int, default=10, help="cuántas líneas (default: 10)")
